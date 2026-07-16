from typing import Literal, Optional, override

from discord import Member

from commanderbot.ext.automod.actions.abc import AddRolesToTarget
from commanderbot.ext.automod.automod_context import AutomodContext
from commanderbot.lib.predicates import is_member

__all__ = ("AddRolesToActor",)


class AddRolesToActor(AddRolesToTarget):
    """
    Add roles to the actor in context.
    """

    type: Literal["add_roles_to_actor"]

    @override
    def get_target(self, context: AutomodContext) -> Optional[Member]:
        if (member := context.event.member) and is_member(member):
            return member
