import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional, Self

import aiohttp
from discord.ext import tasks
from discord.utils import utcnow

from commanderbot.lib import USER_AGENT, JsonObject

from .exceptions import MissingFeedHandler, UnknownMinecraftVersionFormat
from .feed_provider_base import FeedProviderBase, FeedProviderOptionsBase
from .utils import FeedHandler, ZendeskArticle

__all__ = (
    "MinecraftBedrockUpdateInfo",
    "MinecraftBedrockUpdatesOptions",
    "MinecraftBedrockUpdates",
)

RELEASE_VERSION_PATTERN = re.compile(r"\d+\.\d+(?:\.\d+)?")
PREVIEW_VERSION_PATTERN = re.compile(r"\d+\.\d+\.\d+\.\d+")

IMAGE_TAG_PATTERN = re.compile(r"<img\ssrc\s*=\s*['\"]([^'\"]*?)['\"][^>]*?>")


@dataclass
class MinecraftBedrockUpdateInfo:
    title: str
    description: str
    published: datetime
    url: str
    version: str
    thumbnail_url: Optional[str] = None


@dataclass
class MinecraftBedrockUpdatesOptions(FeedProviderOptionsBase):
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
                icon_url=data["icon_url"],
                release_section_id=data["release_section_id"],
                preview_section_id=data["preview_section_id"],
                release_icon_url=data["release_icon_url"],
                preview_icon_url=data["preview_icon_url"],
            )


class MinecraftBedrockUpdates(FeedProviderBase[MinecraftBedrockUpdatesOptions, int]):
    def __init__(self, url: str, release_section_id: int, preview_section_id: int):
        super().__init__(
            url=url, logger_name="commanderbot.ext.feeds.minecraft_bedrock_updates"
        )
        self.release_section_id: int = release_section_id
        self.preview_section_id: int = preview_section_id

        self.release_handler: Optional[FeedHandler[MinecraftBedrockUpdateInfo]] = None
        self.preview_handler: Optional[FeedHandler[MinecraftBedrockUpdateInfo]] = None

        self._etag: Optional[str] = None

    @classmethod
    def from_options(cls, options: MinecraftBedrockUpdatesOptions) -> Self:
        return cls(
            url=options.url,
            release_section_id=options.release_section_id,
            preview_section_id=options.preview_section_id,
        )

    async def _fetch_latest_changelogs(self) -> list[ZendeskArticle]:
        new_changelogs = []
        async with aiohttp.ClientSession(headers={"User-Agent": USER_AGENT}) as session:
            async with session.get(
                self.url, headers={"If-None-Match": self._etag or ""}
            ) as response:
                # Store the status code and other response header data
                self.prev_status_code = response.status
                self._etag = response.headers.get("ETag")

                # Return early if we didn't get an `OK` response
                if self.prev_status_code != 200:
                    return []

                # Add any new changelogs to the cache and the returned array
                changelogs: JsonObject = await response.json()
                changelog_gen = (
                    ZendeskArticle.from_data(raw_changelog)
                    for raw_changelog in changelogs.get("articles", [])
                )
                for changelog in changelog_gen:
                    if changelog.id not in self._cache:
                        self._cache.add(changelog.id)
                        new_changelogs.append(changelog)

        return new_changelogs

    @tasks.loop(minutes=2)
    async def _on_poll(self):
        # Populate the cache on the first time we poll and immediately return
        if not self.prev_status_code:
            self._log.info("Building changelog cache...")
            await self._fetch_latest_changelogs()
            self._log.info(
                f"Done building changelog cache (Initial size: {len(self._cache)})"
            )
            return

        # Try to get the latest changelogs
        self._log.debug("Polling for new changelogs...")
        new_changelogs = await self._fetch_latest_changelogs()
        self._log.debug(f"Found {len(new_changelogs)} new changelogs")

        self.prev_request_date = utcnow()
        self.next_request_date = self._on_poll.next_iteration

        # Process changelogs
        for changelog in new_changelogs:
            # Skip changelog if it's for Java
            if self._is_java_changelog(changelog):
                self._log.debug(f"Skipping changelog: {changelog.title}")
                continue

            # Create update info
            update_info = MinecraftBedrockUpdateInfo(
                title=changelog.title,
                description="",
                published=changelog.created_at,
                url=changelog.html_url,
                version=self._get_version(changelog),
                thumbnail_url=self._get_thumbnail(changelog),
            )

            # Send update to the handlers
            is_release: bool = changelog.section_id == self.release_section_id
            is_preview: bool = changelog.section_id == self.preview_section_id
            if is_release and self.release_handler:
                await self.release_handler(update_info)
            elif is_preview and self.preview_handler:
                await self.preview_handler(update_info)
            else:
                raise MissingFeedHandler

    def _is_java_changelog(self, changelog: ZendeskArticle) -> bool:
        return "java" in changelog.title.lower() or "java" in changelog.name.lower()

    def _get_version(self, changelog: ZendeskArticle) -> str:
        if match := PREVIEW_VERSION_PATTERN.search(changelog.title):
            return match.group(0)
        elif match := RELEASE_VERSION_PATTERN.search(changelog.title):
            return match.group(0)
        else:
            raise UnknownMinecraftVersionFormat(changelog.title)

    def _get_thumbnail(self, changelog: ZendeskArticle) -> Optional[str]:
        if match := IMAGE_TAG_PATTERN.search(changelog.body):
            return match.group(1)
