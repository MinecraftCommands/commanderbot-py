from dataclasses import dataclass
from datetime import datetime
from typing import Optional, override

from discord import Thread

from commanderbot.ext.automod.event import AutomodEvent
from commanderbot.lib.types import MessageableGuildChannel

__all__ = ("GuildChannelPinsUpdated",)


@dataclass
class GuildChannelPinsUpdated(AutomodEvent):
    _channel: MessageableGuildChannel | Thread
    last_pin: Optional[datetime]

    @property
    @override
    def channel(self) -> MessageableGuildChannel | Thread:
        return self._channel
