from typing import Literal, Optional, override

from commanderbot.ext.automod.automod_context import AutomodContext
from commanderbot.ext.automod.condition import AutomodCondition
from commanderbot.ext.automod.guards import IntegerRangeGuard

__all__ = ("MessageHasAttachments",)


class MessageHasAttachments(AutomodCondition):
    """
    Check if the message has attachments.
    """

    type: Literal["message_has_attachments"]

    count: Optional[IntegerRangeGuard] = None
    """The number of attachments to check for. If empty, the message only needs a single attachment."""

    @override
    async def check(self, context: AutomodContext) -> bool:
        # We need to have attachments in context
        attachments = context.event.attachments
        if not attachments:
            return False

        # Check if the number of attachments is in the range
        if self.count:
            attachment_count = len(attachments)
            return self.count.includes(attachment_count)

        # Otherwise, return `True` since we have some number of attachments
        return True
