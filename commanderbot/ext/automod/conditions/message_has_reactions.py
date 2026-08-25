from typing import Literal, Optional, override

from commanderbot.ext.automod.automod_context import AutomodContext
from commanderbot.ext.automod.condition import AutomodCondition
from commanderbot.ext.automod.guards import ReactionsGuard

__all__ = ("MessageHasReactions",)


class MessageHasReactions(AutomodCondition):
    """
    Check if the message has reactions.
    """

    type: Literal["message_has_reactions"]

    reactions: Optional[ReactionsGuard] = None
    """The reactions to match against. If empty, all reactions will match."""

    @override
    async def check(self, context: AutomodContext) -> bool:
        # We need a message in context
        message = context.event.message
        if not message:
            return False

        # Get the reactions from the message and maybe filter out the ones we care about
        reactions = message.reactions
        if self.reactions:
            reactions = self.reactions.filter_reactions(reactions)

        # Check if we have any reactions
        return len(reactions) > 0
