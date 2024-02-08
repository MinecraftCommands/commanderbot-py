import asyncio
import json
import re
from collections import deque
from dataclasses import dataclass
from datetime import datetime
from logging import Logger, getLogger
from typing import Any, Callable, Coroutine, Optional, Self, TypeAlias
from urllib.parse import urlparse, urlunparse

import aiohttp
import feedparser
from discord.ext.tasks import loop
from discord.utils import utcnow

from commanderbot.ext.feeds.providers.utils import (
    MissingFeedHandler,
    RSSFeedItem,
    ZendeskArticle,
)
from commanderbot.lib import FromDataMixin
from commanderbot.lib.constants import USER_AGENT
from commanderbot.lib.types import JsonObject

__all__ = (
    "MinecraftUpdateInfo",
    "MinecraftUpdateHandler",
    "MinecraftJavaUpdatesOptions",
    "MinecraftBedrockUpdatesOptions",
    "MinecraftJavaUpdates",
    "MinecraftBedrockUpdates",
)

CACHE_SIZE: int = 50

JAVA_RELEASE_VERSION_PATTERN = re.compile(r"\d+\.\d+(?:\.\d+)?")
JAVA_SNAPSHOT_VERSION_PATTERN = re.compile(r"\d\dw\d\d[a-z]")
JAVA_PRE_RELEASE_VERSION_PATTERN = re.compile(
    r"\d+\.\d+(?:\.\d+)?[_\-\s]pre[_\-\s]release[_\-\s]\d+", flags=re.IGNORECASE
)
JAVA_RELEASE_CANDIDATE_VERSION_PATTERN = re.compile(
    r"\d+\.\d+(?:\.\d+)?[_\-\s]release[_\-\s]candidate[_\-\s]\d+", flags=re.IGNORECASE
)

BEDROCK_RELEASE_VERSION_PATTERN = re.compile(r"\d+\.\d+(?:\.\d+)?")
BEDROCK_PREVIEW_VERSION_PATTERN = re.compile(r"\d+\.\d+\.\d+\.\d+")

IMAGE_TAG_PATTERN = re.compile(r"<img\ssrc\s*=\s*['\"]([^'\"]*?)['\"][^>]*?>")


class UnknownMinecraftVersionFormat(Exception):
    def __init__(self, version: str):
        self.version: str = version
        super().__init__(f"Could not a find a Minecraft version in: `{self.version}`")


@dataclass
class MinecraftUpdateInfo:
    title: str
    description: str
    published: datetime
    url: str
    version: str
    thumbnail_url: Optional[str] = None


MinecraftUpdateHandler: TypeAlias = Callable[
    [MinecraftUpdateInfo], Coroutine[Any, Any, None]
]


@dataclass
class MinecraftJavaUpdatesOptions(FromDataMixin):
    feed_url: str
    feed_icon_url: str
    release_icon_url: str
    snapshot_icon_url: str

    image_proxy: Optional[str] = None
    cache_size: int = CACHE_SIZE

    # @overrides FromDataMixin
    @classmethod
    def try_from_data(cls, data: Any) -> Optional[Self]:
        if isinstance(data, dict):
            return cls(
                feed_url=data["feed_url"],
                feed_icon_url=data["feed_icon_url"],
                release_icon_url=data["release_icon_url"],
                snapshot_icon_url=data["snapshot_icon_url"],
                image_proxy=data.get("image_proxy"),
                cache_size=data.get("cache_size", CACHE_SIZE),
            )


@dataclass
class MinecraftBedrockUpdatesOptions(FromDataMixin):
    feed_url: str
    feed_icon_url: str
    release_section_id: int
    preview_section_id: int
    release_icon_url: str
    preview_icon_url: str

    image_proxy: Optional[str] = None
    cache_size: int = CACHE_SIZE

    # @overrides FromDataMixin
    @classmethod
    def try_from_data(cls, data: Any) -> Optional[Self]:
        if isinstance(data, dict):
            return cls(
                feed_url=data["feed_url"],
                feed_icon_url=data["feed_icon_url"],
                release_section_id=data["release_section_id"],
                preview_section_id=data["preview_section_id"],
                release_icon_url=data["release_icon_url"],
                preview_icon_url=data["preview_icon_url"],
                image_proxy=data.get("image_proxy"),
                cache_size=data.get("cache_size", CACHE_SIZE),
            )


class MinecraftJavaUpdates:
    def __init__(
        self,
        url: str,
        *,
        image_proxy: Optional[str] = None,
        cache_size: int = CACHE_SIZE,
    ):
        self.url: str = url
        self.prev_status_code: Optional[int] = None
        self.prev_request_date: Optional[datetime] = None
        self.next_request_date: Optional[datetime] = None

        self.release_handler: Optional[MinecraftUpdateHandler] = None
        self.snapshot_handler: Optional[MinecraftUpdateHandler] = None

        self._log: Logger = getLogger("FeedsCog.MinecraftJavaUpdates")
        self._etag: Optional[str] = None
        self._last_modified: Optional[str] = None
        self._image_proxy: Optional[str] = image_proxy
        self._cache: deque[str] = deque(maxlen=cache_size)

    @classmethod
    def from_options(cls, options: MinecraftJavaUpdatesOptions) -> Self:
        return cls(
            url=options.feed_url,
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
        # Try fetching the latest articles
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

        self.prev_status_code = rss_feed["status"]
        self._etag = rss_feed.get("etag")
        self._last_modified = rss_feed.get("modified")

        # Return early if we don't get an `OK` response
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

    @loop(minutes=1)
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
            update_info = MinecraftUpdateInfo(
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
        if match := JAVA_SNAPSHOT_VERSION_PATTERN.search(query):
            return (match.group(0), True)
        elif match := JAVA_PRE_RELEASE_VERSION_PATTERN.search(query):
            return (match.group(0), True)
        elif match := JAVA_RELEASE_CANDIDATE_VERSION_PATTERN.search(query):
            return (match.group(0), True)
        elif match := JAVA_RELEASE_VERSION_PATTERN.search(query):
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


class MinecraftBedrockUpdates:
    def __init__(
        self,
        url: str,
        release_section_id: int,
        preview_section_id: int,
        *,
        image_proxy: Optional[str] = None,
        cache_size: int = CACHE_SIZE,
    ):
        self.url: str = url
        self.release_section_id: int = release_section_id
        self.preview_section_id: int = preview_section_id
        self.prev_status_code: Optional[int] = None
        self.prev_request_date: Optional[datetime] = None
        self.next_request_date: Optional[datetime] = None

        self.release_handler: Optional[MinecraftUpdateHandler] = None
        self.preview_handler: Optional[MinecraftUpdateHandler] = None

        self._log: Logger = getLogger("FeedsCog.MinecraftBedrockUpdates")
        self._etag: Optional[str] = None
        self._image_proxy: Optional[str] = image_proxy
        self._cache: deque[int] = deque(maxlen=cache_size)

    @classmethod
    def from_options(cls, options: MinecraftBedrockUpdatesOptions) -> Self:
        return cls(
            url=options.feed_url,
            release_section_id=options.release_section_id,
            preview_section_id=options.preview_section_id,
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

    async def _fetch_latest_articles(self) -> list[ZendeskArticle]:
        # Try fetching the latest articles
        new_articles = []
        async with aiohttp.ClientSession() as session:
            headers = {"User-Agent": USER_AGENT, "If-None-Match": self._etag or ""}
            async with session.get(self.url, headers=headers) as response:
                self.prev_status_code = response.status
                self._etag = response.headers.get("etag")

                # Return early if we don't get an `OK` response
                if self.prev_status_code != 200:
                    return []

                # Add any new articles to the cache and the returned array
                # response_json: JsonObject = await response.json() # This is a hack for testing
                response_json: JsonObject = json.loads(await response.text())
                article_gen = (
                    ZendeskArticle.from_data(raw_article)
                    for raw_article in response_json.get("articles", [])
                )
                for article in article_gen:
                    if article.id not in self._cache:
                        self._cache.append(article.id)
                        new_articles.append(article)

        return new_articles

    @loop(minutes=1)
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

        # Process update articles
        for article in new_articles:
            # Skip article if it's for Java
            if self._is_java_update_article(article):
                self._log.debug(f"Skipping article: {article.title}")
                continue

            # Create update info
            update_info = MinecraftUpdateInfo(
                title=article.title,
                description="",
                published=article.created_at,
                url=article.html_url,
                version=self._get_version(article),
                thumbnail_url=self._get_thumbnail(article),
            )

            # Send update to the handlers
            if article.section_id == self.release_section_id and self.release_handler:
                await self.release_handler(update_info)
            elif article.section_id == self.preview_section_id and self.preview_handler:
                await self.preview_handler(update_info)
            else:
                raise MissingFeedHandler

    def _is_java_update_article(self, article: ZendeskArticle) -> bool:
        return "java" in article.title.lower() or "java" in article.name.lower()

    def _get_version(self, article: ZendeskArticle) -> str:
        if match := BEDROCK_PREVIEW_VERSION_PATTERN.search(article.title):
            return match.group(0)
        elif match := BEDROCK_RELEASE_VERSION_PATTERN.search(article.title):
            return match.group(0)
        else:
            raise UnknownMinecraftVersionFormat(article.title)

    def _get_thumbnail(self, article: ZendeskArticle) -> Optional[str]:
        if match := IMAGE_TAG_PATTERN.search(article.body):
            thumbnail_url = match.group(1)
            if self._image_proxy:
                return self._image_proxy.format(url=thumbnail_url)
            return thumbnail_url
