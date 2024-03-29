import asyncio
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional, Self
from urllib.parse import urlparse, urlunparse

import feedparser
from discord.ext import tasks
from discord.utils import utcnow

from commanderbot.lib import USER_AGENT

from .exceptions import MissingFeedHandler, UnknownMinecraftVersionFormat
from .feed_provider_base import FeedProviderBase, FeedProviderOptionsBase
from .utils import FeedHandler, RSSFeedItem

__all__ = (
    "MinecraftJavaUpdateInfo",
    "MinecraftJavaUpdatesOptions",
    "MinecraftJavaUpdates",
)

CACHE_SIZE: int = 100

RELEASE_VERSION_PATTERN = re.compile(r"\d+\.\d+(?:\.\d+)?")
SNAPSHOT_VERSION_PATTERN = re.compile(r"\d\dw\d\d[a-z]")
PRE_RELEASE_VERSION_PATTERN = re.compile(
    r"\d+\.\d+(?:\.\d+)?[_\-\s]pre[_\-\s]release[_\-\s]\d+", flags=re.IGNORECASE
)
JAVA_RELEASE_CANDIDATE_VERSION_PATTERN = re.compile(
    r"\d+\.\d+(?:\.\d+)?[_\-\s]release[_\-\s]candidate[_\-\s]\d+", flags=re.IGNORECASE
)


@dataclass
class MinecraftJavaUpdateInfo:
    title: str
    description: str
    published: datetime
    url: str
    version: str
    thumbnail_url: Optional[str] = None


@dataclass
class MinecraftJavaUpdatesOptions(FeedProviderOptionsBase):
    release_icon_url: str
    snapshot_icon_url: str

    image_proxy: Optional[str] = None
    cache_size: int = CACHE_SIZE

    # @overrides FromDataMixin
    @classmethod
    def try_from_data(cls, data: Any) -> Optional[Self]:
        if isinstance(data, dict):
            return cls(
                url=data["url"],
                icon_url=data["icon_url"],
                release_icon_url=data["release_icon_url"],
                snapshot_icon_url=data["snapshot_icon_url"],
                image_proxy=data.get("image_proxy"),
                cache_size=data.get("cache_size", CACHE_SIZE),
            )


class MinecraftJavaUpdates(FeedProviderBase[MinecraftJavaUpdatesOptions, str]):
    def __init__(
        self,
        url: str,
        *,
        image_proxy: Optional[str] = None,
        cache_size: int = CACHE_SIZE,
    ):
        super().__init__(
            url=url,
            logger_name="feeds.minecraft_java_updates",
            cache_size=cache_size,
        )

        self.release_handler: Optional[FeedHandler[MinecraftJavaUpdateInfo]] = None
        self.snapshot_handler: Optional[FeedHandler[MinecraftJavaUpdateInfo]] = None

        self._etag: Optional[str] = None
        self._last_modified: Optional[str] = None
        self._image_proxy: Optional[str] = image_proxy

    @classmethod
    def from_options(cls, options: MinecraftJavaUpdatesOptions) -> Self:
        return cls(
            url=options.url,
            image_proxy=options.image_proxy,
            cache_size=options.cache_size,
        )

    def start(self):
        self._log.info("Started polling for updates...")
        self._poll_for_updates.start()

    def stop(self):
        self._log.info("Stopped polling for updates")
        self._poll_for_updates.stop()

    def restart(self):
        self._log.info("Restarting...")
        self._poll_for_updates.restart()

    async def _fetch_latest_articles(self) -> list[RSSFeedItem]:
        new_articles = []
        loop = asyncio.get_running_loop()
        rss_feed: dict = await loop.run_in_executor(
            None,
            feedparser.parse,
            self.url,
            self._etag,
            self._last_modified,
            USER_AGENT,
        )

        # Store the status code and other response header data
        self.prev_status_code = rss_feed["status"]
        self._etag = rss_feed.get("etag")
        self._last_modified = rss_feed.get("modified")

        # Return early if we didn't get an `OK` response
        if self.prev_status_code != 200:
            return []

        # Add any new articles to the cache and the returned array
        article_gen = (
            RSSFeedItem.from_data(raw_article)
            for raw_article in rss_feed.get("entries", [])
        )
        for article in article_gen:
            if article.id and article.id not in self._cache:
                self._cache.append(article.id)
                new_articles.append(article)

        return new_articles

    @tasks.loop(minutes=5)
    async def _poll_for_updates(self):
        # Populate the cache on the first time we poll and immediately return
        if not self.prev_status_code:
            self._log.info("Building article cache...")
            await self._fetch_latest_articles()
            self._log.info(
                f"Done building article cache (Initial size: {len(self._cache)})"
            )
            return

        # Try to get the latest articles
        self._log.debug("Polling for new articles...")
        new_articles = await self._fetch_latest_articles()
        self._log.debug(f"Found {len(new_articles)} new articles")

        self.prev_request_date = utcnow()
        self.next_request_date = self._poll_for_updates.next_iteration

        # Process articles
        for article in new_articles:
            # Skip article if it doesn't have `primary_tag` or it's not news
            if not article.primary_tag or article.primary_tag.lower() != "news":
                self._log.debug(f"Skipping article: {article.title}")
                continue

            # Skip article if it isn't for Java
            if not self._is_java_update_article(article):
                self._log.debug(f"Skipping article: {article.title}")
                continue

            # Create update info
            version, is_snapshot = self._get_version(article)
            update_info = MinecraftJavaUpdateInfo(
                title=article.title,
                description=article.description,
                published=article.published,
                url=article.link,
                version=version,
                thumbnail_url=self._get_thumbnail(article),
            )

            # Send update to the handlers
            if not is_snapshot and self.release_handler:
                await self.release_handler(update_info)
            elif is_snapshot and self.snapshot_handler:
                await self.snapshot_handler(update_info)
            else:
                raise MissingFeedHandler

    def _is_java_update_article(self, article: RSSFeedItem) -> bool:
        query = f"{article.title} {article.description} {article.link}".lower()

        # `java` must exist
        if "java" not in query:
            return False

        # Check for words related to Bedrock or Realms
        if "beta" in query or "preview" in query or "realms" in query:
            return False

        # Must have a combination of `java` and `snapshot|release|candidate`
        return "snapshot" in query or "release" in query or "candidate" in query

    def _get_version(self, article: RSSFeedItem) -> tuple[str, bool]:
        query = f"{article.title} {article.description} {article.link}"
        if match := SNAPSHOT_VERSION_PATTERN.search(query):
            return (match.group(0), True)
        elif match := PRE_RELEASE_VERSION_PATTERN.search(query):
            return (match.group(0), True)
        elif match := JAVA_RELEASE_CANDIDATE_VERSION_PATTERN.search(query):
            return (match.group(0), True)
        elif match := RELEASE_VERSION_PATTERN.search(query):
            return (match.group(0), False)
        raise UnknownMinecraftVersionFormat(query)

    def _get_thumbnail(self, article: RSSFeedItem) -> Optional[str]:
        if article.image_url:
            url_parts = urlparse(article.link)
            url_parts = url_parts._replace(path=article.image_url)
            thumbnail_url = urlunparse(url_parts).replace(" ", "%20")
            if self._image_proxy:
                return self._image_proxy.format(url=thumbnail_url)
            return thumbnail_url
