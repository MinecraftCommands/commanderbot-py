from typing import Literal, Optional, override

from discord import Member, User

from commanderbot.ext.automod.automod_context import AutomodContext
from commanderbot.ext.automod.conditions.abc import TargetHasAllFlags

__all__ = ("ActorHasAllFlags",)


class ActorHasAllFlags(TargetHasAllFlags):
    """
    Check if the actor has all flags from a selection.
    """

    type: Literal["actor_has_all_flags"] = "actor_has_all_flags"

    @override
    def get_target(self, context: AutomodContext) -> Optional[User | Member]:
        return context.event.actor
