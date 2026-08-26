from typing import Literal, Optional, override

from discord import User

from commanderbot.ext.automod.automod_context import AutomodContext
from commanderbot.ext.automod.conditions.abc import TargetIsBot
from commanderbot.lib.predicates import is_user

__all__ = ("AuthorIsBot",)


class AuthorIsBot(TargetIsBot):
    """
    Check if the author is a bot.
    """

    type: Literal["author_is_bot"]

    @override
    def get_target(self, context: AutomodContext) -> Optional[User]:
        if (user := context.event.author) and is_user(user):
            return user
