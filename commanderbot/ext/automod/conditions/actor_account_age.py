from typing import Literal, Optional, override

from discord import User

from commanderbot.ext.automod.automod_context import AutomodContext
from commanderbot.ext.automod.conditions.abc import TargetAccountAge
from commanderbot.lib.predicates import is_user

__all__ = ("ActorAccountAge",)


class ActorAccountAge(TargetAccountAge):
    """
    Check if the actor's account is a certain age.
    """

    type: Literal["actor_account_age"]

    @override
    def get_target(self, context: AutomodContext) -> Optional[User]:
        if (user := context.event.actor) and is_user(user):
            return user
