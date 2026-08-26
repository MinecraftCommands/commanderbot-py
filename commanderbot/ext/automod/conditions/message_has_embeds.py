from typing import Literal, Optional, override

from commanderbot.ext.automod.automod_context import AutomodContext
from commanderbot.ext.automod.condition import AutomodCondition
from commanderbot.ext.automod.guards import IntegerRangeGuard

__all__ = ("MessageHasEmbeds",)


class MessageHasEmbeds(AutomodCondition):
    """
    Check if the message has embeds.
    """

    type: Literal["message_has_embeds"]

    count: Optional[IntegerRangeGuard] = None
    """The number of embeds to check for. If empty, the message only needs a single embed."""

    @override
    async def check(self, context: AutomodContext) -> bool:
        message = context.event.message
        if not message:
            return False

        embed_count = len(message.embeds)
        if self.count:
            return self.count.includes(embed_count)
        return embed_count > 0
