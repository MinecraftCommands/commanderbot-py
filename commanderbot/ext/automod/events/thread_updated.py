from dataclasses import dataclass
from typing import override

from discord import Thread

from commanderbot.ext.automod.event import AutomodEvent

__all__ = ("ThreadUpdated",)


@dataclass
class ThreadUpdated(AutomodEvent):
    before: Thread
    """The thread's old info."""

    after: Thread
    """The thread's updated info."""

    @property
    @override
    def channel(self) -> Thread:
        return self.after

    @property
    @override
    def thread(self) -> Thread:
        return self.after
