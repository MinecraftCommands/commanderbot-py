from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional, Self

import aiohttp
from discord.ext import tasks
from discord.utils import utcnow

from commanderbot.lib import USER_AGENT
from commanderbot.lib.types import JsonObject

from .exceptions import MissingFeedHandler
from .feed_provider_base import FeedProviderBase, FeedProviderOptionsBase
from .utils import FeedHandler, MinecraftJavaChangelog

__all__ = (
    "MinecraftJavaUpdateInfo",
    "MinecraftJavaUpdatesOptions",
    "MinecraftJavaUpdates",
)


@dataclass
class MinecraftJavaUpdateInfo:
    title: str
    description: str
    published: datetime
    url: str
    version: str
    thumbnail_url: str
    mirror_url: Optional[str] = None


@dataclass
class MinecraftJavaUpdatesOptions(FeedProviderOptionsBase):
    release_icon_url: str
    snapshot_icon_url: str
    primary_changelog_viewer_url: str
    mirror_changelog_viewer_url: Optional[str]

    # @overrides FromDataMixin
    @classmethod
    def try_from_data(cls, data: Any) -> Optional[Self]:
        if isinstance(data, dict):
            raw_changelog_viewer: dict = data["changelog_viewer"]
            return cls(
                url=data["url"],
                icon_url=data["icon_url"],
                release_icon_url=data["release_icon_url"],
                snapshot_icon_url=data["snapshot_icon_url"],
                primary_changelog_viewer_url=raw_changelog_viewer["primary_url"],
                mirror_changelog_viewer_url=raw_changelog_viewer.get("mirror_url"),
            )


class MinecraftJavaUpdates(FeedProviderBase[MinecraftJavaUpdatesOptions, str]):
    def __init__(
        self,
        url: str,
        primary_changelog_viewer_url: str,
        mirror_changelog_viewer_url: Optional[str] = None,
    ):
        super().__init__(url=url, logger_name="feeds.minecraft_java_updates")
        self._primary_changelog_viewer_url: str = primary_changelog_viewer_url
        self._mirror_changelog_viewer_url: Optional[str] = mirror_changelog_viewer_url

        self.release_handler: Optional[FeedHandler[MinecraftJavaUpdateInfo]] = None
        self.snapshot_handler: Optional[FeedHandler[MinecraftJavaUpdateInfo]] = None

        self._last_modified: Optional[str] = None

    @classmethod
    def from_options(cls, options: MinecraftJavaUpdatesOptions) -> Self:
        return cls(
            url=options.url,
            primary_changelog_viewer_url=options.primary_changelog_viewer_url,
            mirror_changelog_viewer_url=options.mirror_changelog_viewer_url,
        )

    async def _fetch_latest_changelogs(self) -> list[MinecraftJavaChangelog]:
        new_changelogs = []
        async with aiohttp.ClientSession(headers={"User-Agent": USER_AGENT}) as session:
            async with session.get(
                self.url, headers={"If-Modified-Since": self._last_modified or ""}
            ) as response:
                # Store the status code and other response header data
                self.prev_status_code = response.status
                self._last_modified = response.headers.get("Last-Modified")

                # Return early if we didn't get an `OK` response
                if self.prev_status_code != 200:
                    return []

                # Add any new changelogs to the cache and the returned array
                changelogs: JsonObject = await response.json()
                changelog_gen = (
                    MinecraftJavaChangelog.from_data(raw_changelog)
                    for raw_changelog in changelogs.get("entries", [])
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
            # Create update info
            update_info = MinecraftJavaUpdateInfo(
                title=changelog.title,
                description=changelog.short_text,
                published=changelog.date,
                url=self._get_primary_url(changelog),
                mirror_url=self._get_mirror_url(changelog),
                version=changelog.version,
                thumbnail_url=(self.base_url + changelog.image_url),
            )

            # Send update to the handlers
            if changelog.is_release and self.release_handler:
                await self.release_handler(update_info)
            elif changelog.is_snapshot and self.snapshot_handler:
                await self.snapshot_handler(update_info)
            else:
                raise MissingFeedHandler

    def _get_primary_url(self, changelog: MinecraftJavaChangelog) -> str:
        return self._primary_changelog_viewer_url.format(version=changelog.version)

    def _get_mirror_url(self, changelog: MinecraftJavaChangelog) -> Optional[str]:
        if self._mirror_changelog_viewer_url:
            return self._mirror_changelog_viewer_url.format(version=changelog.version)
