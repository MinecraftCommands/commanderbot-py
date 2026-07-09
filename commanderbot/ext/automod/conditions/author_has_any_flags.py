from typing import Literal, Optional, override

from discord import Member, User

from commanderbot.ext.automod.automod_context import AutomodContext
from commanderbot.ext.automod.conditions.abc import TargetHasAnyFlags

__all__ = ("AuthorHasAnyFlags",)


class AuthorHasAnyFlags(TargetHasAnyFlags):
    """
    Check if the author has a number of flags from a selection.
    """

    type: Literal["author_has_any_flags"] = "author_has_any_flags"

    @override
    def get_target(self, context: AutomodContext) -> Optional[User | Member]:
        return context.event.author
