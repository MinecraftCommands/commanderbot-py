from abc import abstractmethod
from typing import Optional, override

from discord import Member, User
from pydantic import PositiveInt

from commanderbot.ext.automod.automod_context import AutomodContext
from commanderbot.ext.automod.condition import AutomodCondition
from commanderbot.ext.automod.guards import FlagsGuard

__all__ = ("TargetHasAnyFlags",)


class TargetHasAnyFlags(AutomodCondition):
    flags: FlagsGuard
    """The flags to check."""

    count: PositiveInt = 1
    """The number of flags to check for. If empty, the user/member only needs a single flag."""

    @abstractmethod
    def get_target(self, context: AutomodContext) -> Optional[User | Member]:
        pass

    @override
    async def check(self, context: AutomodContext) -> bool:
        if actor := self.get_target(context):
            return self.flags.has_any(actor, count=self.count)
        return False
