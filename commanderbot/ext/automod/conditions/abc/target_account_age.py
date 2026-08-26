from abc import abstractmethod
from typing import Optional, override

from discord import User
from discord.utils import utcnow

from commanderbot.ext.automod.automod_context import AutomodContext
from commanderbot.ext.automod.condition import AutomodCondition
from commanderbot.lib.timedelta import Timedelta

__all__ = ("TargetAccountAge",)


class TargetAccountAge(AutomodCondition):
    at_least: Optional[Timedelta] = None
    """The lower bound to check against, if any (inclusive)."""

    at_most: Optional[Timedelta] = None
    """The upper bound to check against, if any (inclusive)."""

    @abstractmethod
    def get_target(self, context: AutomodContext) -> Optional[User]: ...

    @override
    async def check(self, context: AutomodContext) -> bool:
        user = self.get_target(context)
        if not user:
            return False

        now = utcnow()
        account_age = now - user.created_at

        if self.at_least is not None and account_age < self.at_least:
            return False

        if self.at_most is not None and account_age > self.at_most:
            return False

        return True
