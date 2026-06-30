from dataclasses import dataclass
from typing import override

from discord import Member, Thread, ThreadMember, User

from commanderbot.ext.automod.event import AutomodEvent
from commanderbot.lib.predicates import is_member, is_user

__all__ = ("ThreadMemberLeft",)


@dataclass
class ThreadMemberLeft(AutomodEvent):
    _member: ThreadMember

    @property
    @override
    def channel(self) -> Thread:
        return self._member.thread

    @property
    @override
    def thread(self) -> Thread:
        return self._member.thread

    @property
    @override
    def actor(self) -> Member:
        return self.member

    @property
    @override
    def member(self) -> Member:
        # ... We still need to do this?
        member = self._member.thread.guild.get_member(self._member.id)
        assert is_member(member)
        return member

    @property
    @override
    def user(self) -> User:
        assert is_user(self.member)
        return self.member
