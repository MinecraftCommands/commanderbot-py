from typing import Literal, Optional, override

from discord import User

from commanderbot.ext.automod.automod_context import AutomodContext
from commanderbot.ext.automod.conditions.abc import TargetIsBot
from commanderbot.lib.predicates import is_user

__all__ = ("ActorIsBot",)


class ActorIsBot(TargetIsBot):
    """
    Check if the actor is a bot.
    """

    type: Literal["actor_is_bot"]

    @override
    def get_target(self, context: AutomodContext) -> Optional[User]:
        if (user := context.event.actor) and is_user(user):
            return user
