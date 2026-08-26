from dataclasses import dataclass
from typing import override

from commanderbot.ext.automod.event import AutomodEvent
from commanderbot.lib.types import GuildChannel

__all__ = ("GuildChannelUpdated",)


@dataclass
class GuildChannelUpdated(AutomodEvent):
    before: GuildChannel
    """The guild channel's old info."""

    after: GuildChannel
    """The guild channel's updated info."""

    @property
    @override
    def channel(self) -> GuildChannel:
        return self.after
