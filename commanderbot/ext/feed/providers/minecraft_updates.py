import json
import re
from collections import deque
from dataclasses import dataclass
from datetime import datetime
from logging import Logger, getLogger
from typing import Any, Callable, Coroutine, Optional, Self, TypeAlias

import aiohttp
from discord.ext.tasks import loop
from discord.utils import utcnow

from commanderbot.ext.feed.providers.utils import MissingHandler, ZendeskArticle
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

BEDROCK_RELEASE_VERSION_PATTERN = re.compile(r"\d+\.\d+\.\d+")
BEDROCK_PREVIEW_VERSION_PATTERN = re.compile(r"\d+\.\d+\.\d+\.\d+")
IMAGE_TAG_PATTERN = re.compile(r"<img\ssrc\s*=\s*['\"]([^'\"]*?)['\"][^>]*?>")


@dataclass
class MinecraftUpdateInfo:
    title: str
    summary: str
    published: datetime
    url: str
    version: Optional[str] = None
    thumbnail_url: Optional[str] = None


MinecraftUpdateHandler: TypeAlias = Callable[
    [MinecraftUpdateInfo], Coroutine[Any, Any, None]
]


@dataclass
class MinecraftJavaUpdatesOptions(FromDataMixin):
    url: str
    release_icon_url: str
    snapshot_icon_url: str

    # @overrides FromDataMixin
    @classmethod
    def try_from_data(cls, data: Any) -> Optional[Self]:
        if isinstance(data, dict):
            return cls(
                url=data["url"],
                release_icon_url=data["release_icon_url"],
                snapshot_icon_url=data["snapshot_icon_url"],
            )


@dataclass
class MinecraftBedrockUpdatesOptions(FromDataMixin):
    url: str
    release_section_id: int
    preview_section_id: int
    release_icon_url: str
    preview_icon_url: str

    # @overrides FromDataMixin
    @classmethod
    def try_from_data(cls, data: Any) -> Optional[Self]:
        if isinstance(data, dict):
            return cls(
                url=data["url"],
                release_section_id=data["release_section_id"],
                preview_section_id=data["preview_section_id"],
                release_icon_url=data["release_icon_url"],
                preview_icon_url=data["preview_icon_url"],
            )


class MinecraftJavaUpdates:
    pass


class MinecraftBedrockUpdates:
    def __init__(
        self,
        url: str,
        release_section_id: int,
        preview_section_id: int,
        *,
        cache_size: int = 50,
    ):
        self.url: str = url
        self.release_section_id: int = release_section_id
        self.preview_section_id: int = preview_section_id
        self.prev_status_code: Optional[int] = None
        self.prev_request_date: Optional[datetime] = None
        self.next_request_date: Optional[datetime] = None

        self.release_handler: Optional[MinecraftUpdateHandler] = None
        self.preview_handler: Optional[MinecraftUpdateHandler] = None

        self._log: Logger = getLogger("FeedCog.MinecraftBedrockUpdates")
        self._etag: Optional[str] = None
        self._cache: deque[int] = deque(maxlen=cache_size)

    @classmethod
    def from_options(cls, options: MinecraftBedrockUpdatesOptions) -> Self:
        return cls(
            url=options.url,
            release_section_id=options.release_section_id,
            preview_section_id=options.preview_section_id,
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

    @loop(minutes=1)
    async def _poll_for_updates(self):
        # Populate the cache on the first time we poll and immediately return
        if not self.prev_status_code:
            self._log.info("Building update cache...")
            await self._fetch_latest_updates()
            self._log.info(
                f"Done building update cache (Initial size: {len(self._cache)})"
            )
            return

        # Try to get the articles for the latest updates
        self._log.debug("Polling for new updates...")
        new_articles = await self._fetch_latest_updates()
        self._log.debug(f"Found {len(new_articles)} new updates")

        self.prev_request_date = utcnow()
        self.next_request_date = self._poll_for_updates.next_iteration

        # Process update articles
        for article in new_articles:
            # Skip article if it's for Java
            if self._is_java_article(article):
                self._log.debug(f"Skipping update: {article.title}")
                continue

            # Create update info
            update_info = MinecraftUpdateInfo(
                article.title,
                "",
                article.created_at,
                article.html_url,
                self._get_version(article),
                self._get_thumbnail(article),
            )

            if handler := self._get_handler_for(article):
                await handler(update_info)

    async def _fetch_latest_updates(self) -> list[ZendeskArticle]:
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

    def _is_java_article(self, article: ZendeskArticle) -> bool:
        return "java" in article.title.lower() or "java" in article.name.lower()

    def _get_version(self, article: ZendeskArticle) -> Optional[str]:
        if match := BEDROCK_PREVIEW_VERSION_PATTERN.search(article.title):
            return match.group(0)
        elif match := BEDROCK_RELEASE_VERSION_PATTERN.search(article.title):
            return match.group(0)

    def _get_thumbnail(self, article: ZendeskArticle) -> Optional[str]:
        if match := IMAGE_TAG_PATTERN.search(article.body):
            return match.group(1)

    def _get_handler_for(
        self, article: ZendeskArticle
    ) -> Optional[MinecraftUpdateHandler]:
        match article.section_id:
            case self.release_section_id:
                return self.release_handler
            case self.preview_section_id:
                return self.preview_handler
            case _:
                raise MissingHandler(
                    self.__name__, f"Unknown `section_id` ({article.section_id})"
                )
