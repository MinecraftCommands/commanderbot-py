from typing import Literal, Optional, override

from discord import Member

from commanderbot.ext.automod.automod_context import AutomodContext
from commanderbot.ext.automod.conditions.abc import TargetMemberFor
from commanderbot.lib.predicates import is_member

__all__ = ("ActorMemberFor",)


class ActorMemberFor(TargetMemberFor):
    """
    Check if the actor has been on the server for a certain amount of time.
    """

    type: Literal["actor_member_for"] = "actor_member_for"

    @override
    def get_target(self, context: AutomodContext) -> Optional[Member]:
        if (member := context.event.actor) and is_member(member):
            return member
