from abc import abstractmethod
from typing import Optional, override

from discord import Member, Role
from pydantic import Field

from commanderbot.ext.automod.action import AutomodAction
from commanderbot.ext.automod.automod_context import AutomodContext
from commanderbot.lib.types import RoleID

__all__ = ("AddRolesToTarget",)


class AddRolesToTarget(AutomodAction):
    roles: set[RoleID] = Field(min_length=1)
    """The roles to add."""

    reason: Optional[str] = None
    """The reason why the roles were added, if any."""

    @abstractmethod
    def get_target(self, context: AutomodContext) -> Optional[Member]:
        ...

    @override
    async def apply(self, context: AutomodContext):
        if member := self.get_target(context):
            roles: list[Role] = []
            for role_id in self.roles:
                if role := member.guild.get_role(role_id):
                    roles.append(role)
                else:
                    context.log.exception(f"Failed to resolve role '{role_id}'")

            await member.add_roles(*roles, reason=self.reason)
