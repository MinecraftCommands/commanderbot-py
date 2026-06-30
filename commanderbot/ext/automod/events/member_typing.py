from dataclasses import dataclass
from datetime import datetime
from typing import override

from discord import Member, Thread, User

from commanderbot.ext.automod.event import AutomodEvent
from commanderbot.lib.predicates import is_user
from commanderbot.lib.types import MessageableGuildChannel

__all__ = ("MemberTyping",)


@dataclass
class MemberTyping(AutomodEvent):
    _channel: MessageableGuildChannel | Thread
    _member: Member
    when: datetime

    @property
    @override
    def channel(self) -> MessageableGuildChannel | Thread:
        return self._channel

    @property
    @override
    def actor(self) -> Member:
        return self._member

    @property
    @override
    def member(self) -> Member:
        return self._member

    @property
    @override
    def user(self) -> User:
        assert is_user(self._member)
        return self._member
