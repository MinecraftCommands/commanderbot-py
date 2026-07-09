from typing import Literal, Optional, override

from commanderbot.ext.automod.automod_context import AutomodContext
from commanderbot.ext.automod.condition import AutomodCondition
from commanderbot.ext.automod.guards import IntegerRangeGuard

__all__ = ("MessageHasAttachments",)


class MessageHasAttachments(AutomodCondition):
    """
    Check if the message has attachments.
    """

    type: Literal["message_has_attachments"] = "message_has_attachments"

    count: Optional[IntegerRangeGuard] = None
    """The number of attachments to check for. If empty, the message only needs a single attachment."""

    @override
    async def check(self, context: AutomodContext) -> bool:
        message = context.event.message
        if not message:
            return False

        attachment_count = len(message.attachments)
        if self.count:
            return self.count.includes(attachment_count)
        return attachment_count > 0
