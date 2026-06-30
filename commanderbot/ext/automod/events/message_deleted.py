from dataclasses import dataclass
from typing import Optional, override

from discord import Member, Message, Thread, User

from commanderbot.ext.automod.event import AutomodEvent
from commanderbot.lib.predicates import (
    is_member,
    is_messagable_guild_channel,
    is_thread,
    is_user,
)
from commanderbot.lib.types import MessageableGuildChannel

__all__ = ("MessageDeleted",)


@dataclass
class MessageDeleted(AutomodEvent):
    _message: Message

    @property
    @override
    def channel(self) -> MessageableGuildChannel | Thread:
        assert is_messagable_guild_channel(self._message.channel) or is_thread(
            self._message.channel
        )
        return self._message.channel

    @property
    @override
    def message(self) -> Message:
        return self._message

    @property
    @override
    def author(self) -> Member | User:
        return self._message.author

    @property
    @override
    def actor(self) -> Member | User:
        return self._message.author

    @property
    @override
    def member(self) -> Optional[Member]:
        if is_member(self._message.author):
            return self._message.author

    @property
    @override
    def user(self) -> Optional[User]:
        if is_user(self._message.author):
            return self._message.author
