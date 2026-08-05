from typing import Literal, Optional, override

from discord import User

from commanderbot.ext.automod.actions.abc import DeleteTargetMessages
from commanderbot.ext.automod.automod_context import AutomodContext
from commanderbot.lib.predicates import is_user

__all__ = ("DeleteActorMessages",)


class DeleteActorMessages(DeleteTargetMessages):
    """
    Delete messages from the actor in context that are being tracked by a bucket.
    """

    type: Literal["delete_actor_messages"]

    @override
    def get_target(self, context: AutomodContext) -> Optional[User]:
        if (member := context.event.actor) and is_user(member):
            return member
