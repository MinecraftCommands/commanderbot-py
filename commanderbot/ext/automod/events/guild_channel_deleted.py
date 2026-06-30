from dataclasses import dataclass
from typing import override

from commanderbot.ext.automod.event import AutomodEvent
from commanderbot.lib.types import GuildChannel

__all__ = ("GuildChannelDeleted",)


@dataclass
class GuildChannelDeleted(AutomodEvent):
    _channel: GuildChannel

    @property
    @override
    def channel(self) -> GuildChannel:
        return self._channel
