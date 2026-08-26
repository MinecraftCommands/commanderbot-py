from typing import Literal, Optional, override

from commanderbot.ext.automod.automod_context import AutomodContext
from commanderbot.ext.automod.condition import AutomodCondition
from commanderbot.ext.automod.guards import IntegerRangeGuard

__all__ = ("MessageHasMentions",)


class MessageHasMentions(AutomodCondition):
    """
    Check if the message has mentions.
    """

    type: Literal["message_has_mentions"]

    count: Optional[IntegerRangeGuard] = None
    """The number of mentions to check for. If empty, the message only needs a single mention."""

    @override
    async def check(self, context: AutomodContext) -> bool:
        message = context.event.message
        if not message:
            return False

        role_mention_count = len(message.role_mentions)
        user_mention_count = len(message.mentions)
        mentions = role_mention_count + user_mention_count

        if self.count:
            return self.count.includes(mentions)
        return mentions > 0
