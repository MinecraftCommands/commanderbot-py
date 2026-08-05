from typing import Literal, Optional, override

from discord import Member

from commanderbot.ext.automod.actions.abc import RemoveRolesFromTarget
from commanderbot.ext.automod.automod_context import AutomodContext
from commanderbot.lib.predicates import is_member

__all__ = ("RemoveRolesFromActor",)


class RemoveRolesFromActor(RemoveRolesFromTarget):
    """
    Remove roles from the actor in context.
    """

    type: Literal["remove_roles_from_actor"]

    @override
    def get_target(self, context: AutomodContext) -> Optional[Member]:
        if (member := context.event.actor) and is_member(member):
            return member
