from abc import abstractmethod
from typing import Optional, override

from discord import Member, User

from commanderbot.ext.automod.automod_context import AutomodContext
from commanderbot.ext.automod.condition import AutomodCondition
from commanderbot.ext.automod.guards import FlagsGuard

__all__ = ("TargetHasAllFlags",)


class TargetHasAllFlags(AutomodCondition):
    flags: FlagsGuard
    """The flags to check."""

    @abstractmethod
    def get_target(self, context: AutomodContext) -> Optional[User | Member]:
        pass

    @override
    async def check(self, context: AutomodContext) -> bool:
        if actor := self.get_target(context):
            return self.flags.has_all(actor)
        return False
