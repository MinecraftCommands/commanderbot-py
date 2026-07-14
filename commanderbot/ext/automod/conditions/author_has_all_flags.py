from typing import Literal, Optional, override

from discord import Member, User

from commanderbot.ext.automod.automod_context import AutomodContext
from commanderbot.ext.automod.conditions.abc import TargetHasAllFlags

__all__ = ("AuthorHasAllFlags",)


class AuthorHasAllFlags(TargetHasAllFlags):
    """
    Check if the author has all flags from a selection.
    """

    type: Literal["author_has_all_flags"]

    @override
    def get_target(self, context: AutomodContext) -> Optional[User | Member]:
        return context.event.author
