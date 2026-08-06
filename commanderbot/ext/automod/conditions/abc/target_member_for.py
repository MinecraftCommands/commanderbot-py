from abc import abstractmethod
from typing import Optional, override

from discord import Member
from discord.utils import utcnow

from commanderbot.ext.automod.automod_context import AutomodContext
from commanderbot.ext.automod.condition import AutomodCondition
from commanderbot.lib.types import Timedelta

__all__ = ("TargetMemberFor",)


class TargetMemberFor(AutomodCondition):
    at_least: Optional[Timedelta] = None
    """The lower bound to check against, if any (inclusive)."""

    at_most: Optional[Timedelta] = None
    """The upper bound to check against, if any (inclusive)."""

    @abstractmethod
    def get_target(self, context: AutomodContext) -> Optional[Member]:
        ...

    @override
    async def check(self, context: AutomodContext) -> bool:
        member = self.get_target(context)
        if not member:
            return False

        if member.joined_at is None:
            return False

        now = utcnow()
        member_for = now - member.joined_at

        if self.at_least is not None and member_for < self.at_least:
            return False

        if self.at_most is not None and member_for > self.at_most:
            return False

        return True
