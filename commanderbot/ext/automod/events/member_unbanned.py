from dataclasses import dataclass
from typing import override

from discord import User

from commanderbot.ext.automod.event import AutomodEvent

__all__ = ("MemberUnbanned",)


@dataclass
class MemberUnbanned(AutomodEvent):
    _user: User

    @property
    @override
    def actor(self) -> User:
        return self._user

    @property
    @override
    def user(self) -> User:
        return self._user
