from datetime import datetime
from typing import Optional

import aiohttp
from discord.ext.tasks import loop

from commanderbot.ext.manifest.manifest_data import Version
from commanderbot.lib.constants import USER_AGENT
from commanderbot.lib.utils import datetime_to_int, utcnow_aware


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

    @property
    def prev_request_ts(self) -> Optional[int]:
        if self.prev_request_date:
            return datetime_to_int(self.prev_request_date)

    @property
    def next_request_ts(self) -> Optional[int]:
        if self.next_request_date:
            return datetime_to_int(self.next_request_date)

    @staticmethod
    def default_version() -> Version:
        return Version(1, 19, 0)

    @loop(hours=1)
    async def _update(self):
        # Return eaarly if the URL wasn't set
        if not self.url:
            return

        # Try to update the version
        headers: dict[str, str] = {"User-Agent": USER_AGENT}
        async with aiohttp.ClientSession() as session:
            async with session.get(self.url, headers=headers) as response:
                self.prev_request_date = utcnow_aware()
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
