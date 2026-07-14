from typing import Literal, Optional, override

from commanderbot.ext.automod.automod_context import AutomodContext
from commanderbot.ext.automod.condition import AutomodCondition
from commanderbot.ext.automod.guards import IntegerRangeGuard, RolesGuard

__all__ = ("MessageMentionsRoles",)


class MessageMentionsRoles(AutomodCondition):
    """
    Check if the message contains role mentions.
    """

    type: Literal["message_mentions_roles"]

    roles: Optional[RolesGuard] = None
    """The roles to match against. If empty, all roles will match."""

    count: Optional[IntegerRangeGuard] = None
    """The number of role mentions to check for. If empty, the message only needs a single role mention."""

    @override
    async def check(self, context: AutomodContext) -> bool:
        # Return if the event has no message
        message = context.event.message
        if not message:
            return False

        # Return if the message has no role mentions
        if not message.role_mentions:
            return False

        # Check if we care about any of the mentioned roles
        mentioned_roles = message.role_mentions
        if self.roles:
            mentioned_roles = self.roles.filter_roles(message.role_mentions)

        # Return if we have no role mentions or the number of role mentions is outside
        # the range of the guard
        if not mentioned_roles:
            return False
        if self.count and self.count.excludes(len(mentioned_roles)):
            return False

        # Add mentioned roles metadata to context
        context.set_metadata(
            "mentioned_roles", " ".join((role.mention for role in mentioned_roles))
        )
        context.set_metadata(
            "mentioned_role_names", " ".join((f"`{role}`" for role in mentioned_roles))
        )

        # If we got this far, the message has role mentions we care about
        return True
