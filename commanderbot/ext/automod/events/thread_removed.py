from dataclasses import dataclass
from typing import override

from discord import Thread

from commanderbot.ext.automod.event import AutomodEvent

__all__ = ("ThreadRemoved",)


@dataclass
class ThreadRemoved(AutomodEvent):
    _thread: Thread

    @property
    @override
    def channel(self) -> Thread:
        return self._thread

    @property
    @override
    def thread(self) -> Thread:
        return self._thread
