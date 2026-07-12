from typing import Literal, Optional, override

from discord import User

from commanderbot.ext.automod.automod_context import AutomodContext
from commanderbot.ext.automod.conditions.abc import TargetIsSelf
from commanderbot.lib.predicates import is_user

__all__ = ("AuthorIsNotSelf",)


class AuthorIsNotSelf(TargetIsSelf):
    """
    Check if the author is not the bot itself.
    """

    type: Literal["author_is_not_self"] = "author_is_not_self"

    @override
    def get_target(self, context: AutomodContext) -> Optional[User]:
        if (user := context.event.author) and is_user(user):
            return user
