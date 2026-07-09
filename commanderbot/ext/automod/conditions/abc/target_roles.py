from abc import abstractmethod
from typing import Optional, override

from discord import Member

from commanderbot.ext.automod.automod_context import AutomodContext
from commanderbot.ext.automod.condition import AutomodCondition
from commanderbot.ext.automod.guards import RolesGuard

__all__ = ("TargetRoles",)


class TargetRoles(AutomodCondition):
    roles: RolesGuard
    """The roles to check against."""

    @abstractmethod
    def get_target(self, context: AutomodContext) -> Optional[Member]:
        pass

    @override
    async def check(self, context: AutomodContext) -> bool:
        if member := self.get_target(context):
            return not self.roles.ignore(member)
        return False
