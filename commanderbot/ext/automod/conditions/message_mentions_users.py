from typing import Literal, Optional, override

from commanderbot.ext.automod.automod_context import AutomodContext
from commanderbot.ext.automod.condition import AutomodCondition
from commanderbot.ext.automod.guards import IntegerRangeGuard, RolesGuard

__all__ = ("MessageMentionsUsers",)


class MessageMentionsUsers(AutomodCondition):
    """
    Check if the message contains user mentions.
    """

    type: Literal["message_mentions_users"]

    roles: Optional[RolesGuard] = None
    """The roles of the mentioned users to match against. If empty, all roles will match."""

    count: Optional[IntegerRangeGuard] = None
    """The number of user mentions to check for. If empty, the message only needs a single user mention."""

    @override
    async def check(self, context: AutomodContext) -> bool:
        # Return if the event has no message
        message = context.event.message
        if not message:
            return False

        # Return if the message has no user mentions
        if not message.mentions:
            return False

        # Check if we care about any of the mentioned users
        mentioned_users = message.mentions
        if self.roles:
            mentioned_users = self.roles.filter_members(mentioned_users)

        # Return if we have no user mentions or the number of user mentions is outside
        # the range of the guard
        if not mentioned_users:
            return False
        if self.count and self.count.excludes(len(mentioned_users)):
            return False

        # Add mentioned users metadata to context
        context.set_metadata(
            "mentioned_users", " ".join((user.mention for user in mentioned_users))
        )
        context.set_metadata(
            "mentioned_user_names", " ".join((f"`{user}`" for user in mentioned_users))
        )

        # If we got this far, the message has user mentions we care about
        return True
