from dataclasses import dataclass
from typing import override

from discord import Member, User

from commanderbot.ext.automod.event import AutomodEvent
from commanderbot.lib.predicates import is_user

__all__ = ("MemberJoined",)


@dataclass
class MemberJoined(AutomodEvent):
    _member: Member

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
