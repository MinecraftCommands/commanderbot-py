from typing import Literal, Optional, override

from commanderbot.ext.automod.automod_context import AutomodContext
from commanderbot.ext.automod.condition import AutomodCondition
from commanderbot.ext.automod.guards import IntegerRangeGuard

__all__ = ("MessageHasLinks",)


class MessageHasLinks(AutomodCondition):
    """
    Check if the message has links.
    """

    type: Literal["message_has_links"] = "message_has_links"

    count: Optional[IntegerRangeGuard] = None
    """The number of links to check for. If empty, the message only needs a single link."""

    # TODO Implement a configurable set of allowed domains? #enhance
    # TODO Implement configurable unicode normalization? #enhance

    @override
    async def check(self, context: AutomodContext) -> bool:
        message = context.event.message
        if not message:
            return False

        content = message.content
        http_count = content.count("http://")
        https_count = content.count("https://")
        link_count = http_count + https_count

        if self.count:
            return self.count.includes(link_count)
        return link_count > 0
