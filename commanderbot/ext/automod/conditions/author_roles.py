from typing import Literal, Optional, override

from discord import Member

from commanderbot.ext.automod.automod_context import AutomodContext
from commanderbot.ext.automod.conditions.abc import TargetRoles
from commanderbot.lib.predicates import is_member

__all__ = ("AuthorRoles",)


class AuthorRoles(TargetRoles):
    """
    Check if the author in context has certain roles.
    """

    type: Literal["author_roles"] = "author_roles"

    @override
    def get_target(self, context: AutomodContext) -> Optional[Member]:
        if (member := context.event.author) and is_member(member):
            return member
