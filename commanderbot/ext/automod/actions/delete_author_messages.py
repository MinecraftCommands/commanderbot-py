from typing import Literal, Optional, override

from discord import User

from commanderbot.ext.automod.actions.abc import DeleteTargetMessages
from commanderbot.ext.automod.automod_context import AutomodContext
from commanderbot.lib.predicates import is_user

__all__ = ("DeleteAuthorMessages",)


class DeleteAuthorMessages(DeleteTargetMessages):
    """
    Delete messages from the author in context that are being tracked by a bucket.
    """

    type: Literal["delete_author_messages"]

    @override
    def get_target(self, context: AutomodContext) -> Optional[User]:
        if (member := context.event.author) and is_user(member):
            return member
