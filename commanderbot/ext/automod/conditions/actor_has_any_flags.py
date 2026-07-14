from typing import Literal, Optional, override

from discord import Member, User

from commanderbot.ext.automod.automod_context import AutomodContext
from commanderbot.ext.automod.conditions.abc import TargetHasAnyFlags

__all__ = ("ActorHasAnyFlags",)


class ActorHasAnyFlags(TargetHasAnyFlags):
    """
    Check if the actor has a number of flags from a selection.
    """

    type: Literal["actor_has_any_flags"]

    @override
    def get_target(self, context: AutomodContext) -> Optional[User | Member]:
        return context.event.actor
