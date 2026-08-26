from typing import Literal, Optional, override

from discord import Member

from commanderbot.ext.automod.actions.abc import RemoveRolesFromTarget
from commanderbot.ext.automod.automod_context import AutomodContext
from commanderbot.lib.predicates import is_member

__all__ = ("RemoveRolesFromAuthor",)


class RemoveRolesFromAuthor(RemoveRolesFromTarget):
    """
    Remove roles from the author in context.
    """

    type: Literal["remove_roles_from_author"]

    @override
    def get_target(self, context: AutomodContext) -> Optional[Member]:
        if (member := context.event.author) and is_member(member):
            return member
