import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Coroutine, Optional, Self, TypeAlias

import aiohttp
from discord.ext import tasks
from discord.utils import utcnow

from .feed_provider_base import FeedProviderBase, FeedProviderOptionsBase
from .utils import MinecraftJavaVersion
from commanderbot.lib import JsonObject, USER_AGENT

__all__ = (
    "MinecraftJavaJarUpdateInfo",
    "MinecraftJavaJarUpdatesOptions",
    "MinecraftJavaJarUpdates",
)

CACHE_SIZE: int = 50


@dataclass
class MinecraftJavaJarUpdateInfo:
    version: str
    released: datetime
    url: str
    java_version: int
    client_jar_url: str
    server_jar_url: str
    client_mappings_url: str
    server_mappings_url: str


UpdateHandler: TypeAlias = Callable[
    [MinecraftJavaJarUpdateInfo], Coroutine[Any, Any, None]
]


@dataclass
class MinecraftJavaJarUpdatesOptions(FeedProviderOptionsBase):
    release_jar_icon_url: str
    snapshot_jar_icon_url: str

    cache_size: int = CACHE_SIZE

    # @overrides FromDataMixin
    @classmethod
    def try_from_data(cls, data: Any) -> Optional[Self]:
        if isinstance(data, dict):
            return cls(
                url=data["url"],
                icon_url=data["icon_url"],
                release_jar_icon_url=data["release_jar_icon_url"],
                snapshot_jar_icon_url=data["snapshot_jar_icon_url"],
                cache_size=data.get("cache_size", CACHE_SIZE),
            )


@dataclass
class MinecraftJavaJarUpdates(FeedProviderBase[MinecraftJavaJarUpdatesOptions, str]):
    def __init__(
        self,
        url: str,
        *,
        cache_size: int = CACHE_SIZE,
    ):
        super().__init__(url, "FeedsCog.MinecraftJavaJarUpdates", cache_size)

        self.release_handler: Optional[UpdateHandler] = None
        self.snapshot_handler: Optional[UpdateHandler] = None

        self._last_modified: Optional[str] = None

    @classmethod
    def from_options(cls, options: MinecraftJavaJarUpdatesOptions) -> Self:
        return cls(url=options.url, cache_size=options.cache_size)

    def start(self):
        self._log.info("Started polling for updates...")
        self._poll_for_updates.start()

    def stop(self):
        self._log.info("Stopped polling for updates")
        self._poll_for_updates.stop()

    def restart(self):
        self._log.info("Restarting...")
        self._poll_for_updates.restart()

    async def _fetch_version(
        self, session: aiohttp.ClientSession, url: str
    ) -> Optional[MinecraftJavaVersion]:
        async with session.get(url) as response:
            # Return early if we didn't get an `OK` response
            if response.status != 200:
                return

            # Turn the version Json into a version manifest version
            raw_version: JsonObject = await response.json()
            version = MinecraftJavaVersion.from_data(raw_version)
            version.url = url
            return version

    async def _fetch_latest_versions(self) -> list[MinecraftJavaVersion]:
        new_versions = []
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

                # Add any new versions to the cache and the returned array
                # manifest: JsonObject = await response.json() # This is a hack for testing
                manifest: JsonObject = json.loads(await response.text())
                latest_versions: tuple[str, str] = (
                    manifest["latest"]["release"],
                    manifest["latest"]["snapshot"],
                )

                # Iterate over all versions in the manifest
                versions_gen = (
                    (v["id"], v["url"]) for v in manifest.get("versions", [])
                )
                for id, url in versions_gen:
                    # Skip iteration if the version isn't the latest version
                    if id not in latest_versions:
                        continue

                    # Skip iteration if the version was already cached
                    if id in self._cache:
                        continue

                    # This is a new version, so cache it and request the rest of its data
                    self._cache.append(id)
                    if version := await self._fetch_version(session, url):
                        new_versions.append(version)

        return new_versions

    @tasks.loop(minutes=5)
    async def _poll_for_updates(self):
        # Populate the cache on the first time we poll and immediately return
        if not self.prev_status_code:
            self._log.info("Building version cache...")
            await self._fetch_latest_versions()
            self._log.info(
                f"Done building version cache (Initial size: {len(self._cache)})"
            )
            return

        # Try to get the latest versions
        self._log.debug("Polling for new versions...")
        new_versions = await self._fetch_latest_versions()
        self._log.debug(f"Found {len(new_versions)} new versions")

        self.prev_request_date = utcnow()
        self.next_request_date = self._poll_for_updates.next_iteration

        # Process latest versions
        for version in new_versions:
            # Create jar update info
            is_release: bool = version.type == "release"
            is_snapshot: bool = version.type == "snapshot"
            jar_update_info = MinecraftJavaJarUpdateInfo(
                version=version.id,
                released=version.release_time,
                url=version.url or "",
                java_version=version.java_version,
                client_jar_url=version.client_jar_url,
                server_jar_url=version.server_jar_url,
                client_mappings_url=version.client_mappings_url,
                server_mappings_url=version.server_mappings_url,
            )

            # Send jar update to the handlers
            if is_release and self.release_handler:
                await self.release_handler(jar_update_info)
            elif is_snapshot and self.snapshot_handler:
                await self.snapshot_handler(jar_update_info)
