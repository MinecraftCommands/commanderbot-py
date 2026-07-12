from typing import Literal, Optional, override

from discord import Member

from commanderbot.ext.automod.automod_context import AutomodContext
from commanderbot.ext.automod.conditions.abc import TargetRoles
from commanderbot.lib.predicates import is_member

__all__ = ("ActorRoles",)


class ActorRoles(TargetRoles):
    """
    Check if the actor has certain roles.
    """

    type: Literal["actor_roles"] = "actor_roles"

    @override
    def get_target(self, context: AutomodContext) -> Optional[Member]:
        if (member := context.event.actor) and is_member(member):
            return member
