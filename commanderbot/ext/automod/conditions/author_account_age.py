from typing import Literal, Optional, override

from discord import User

from commanderbot.ext.automod.automod_context import AutomodContext
from commanderbot.ext.automod.conditions.abc import TargetAccountAge
from commanderbot.lib.predicates import is_user

__all__ = ("AuthorAccountAge",)


class AuthorAccountAge(TargetAccountAge):
    """
    Check if the author's account is a certain age.
    """

    type: Literal["author_account_age"]

    @override
    def get_target(self, context: AutomodContext) -> Optional[User]:
        if (user := context.event.author) and is_user(user):
            return user
