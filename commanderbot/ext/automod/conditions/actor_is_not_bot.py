from typing import Literal, Optional, override

from discord import User

from commanderbot.ext.automod.automod_context import AutomodContext
from commanderbot.ext.automod.conditions.abc import TargetIsNotBot
from commanderbot.lib.predicates import is_user

__all__ = ("ActorIsNotBot",)


class ActorIsNotBot(TargetIsNotBot):
    """
    Check if the actor is not a bot.
    """

    type: Literal["actor_is_not_bot"] = "actor_is_not_bot"

    @override
    def get_target(self, context: AutomodContext) -> Optional[User]:
        if (user := context.event.actor) and is_user(user):
            return user
