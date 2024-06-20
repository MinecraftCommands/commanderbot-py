from datetime import datetime
from typing import Optional

import aiohttp
from discord.ext import tasks
from discord.utils import utcnow

from commanderbot.ext.manifest.manifest_data import Version
from commanderbot.lib import constants


class ManifestVersionManager:
    def __init__(self, *, url: Optional[str] = None):
        self.url: Optional[str] = url
        self.prev_request_date: Optional[datetime] = None
        self.next_request_date: Optional[datetime] = None
        self.prev_status_code: Optional[int] = None
        self._latest_version: Optional[Version] = None

    @property
    def latest_version(self) -> Version:
        return self._latest_version or self.default_version()

    @staticmethod
    def default_version() -> Version:
        return Version(1, 20, 0)

    @tasks.loop(hours=1)
    async def _update(self):
        # Return early if the URL wasn't set
        if not self.url:
            return

        # Try to update the version
        headers: dict[str, str] = {"User-Agent": constants.USER_AGENT}
        async with aiohttp.ClientSession() as session:
            async with session.get(self.url, headers=headers) as response:
                self.prev_request_date = utcnow()
                self.next_request_date = self._update.next_iteration
                self.prev_status_code = response.status

                if response.status == 200:
                    if v := Version.from_str(await response.text()):
                        self._latest_version = v

    def start(self):
        self._update.start()

    def stop(self):
        self._update.cancel()

    def restart(self):
        self._update.restart()

    async def update(self):
        await self._update()
        self._update.restart()
