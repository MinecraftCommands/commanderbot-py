from dataclasses import dataclass
from typing import override

from discord import Member, User

from commanderbot.ext.automod.event import AutomodEvent
from commanderbot.lib.predicates import is_user

__all__ = ("MemberUpdated",)


@dataclass
class MemberUpdated(AutomodEvent):
    before: Member
    after: Member

    @property
    @override
    def actor(self) -> Member:
        return self.after

    @property
    @override
    def member(self) -> Member:
        return self.after

    @property
    @override
    def user(self) -> User:
        assert is_user(self.after)
        return self.after
