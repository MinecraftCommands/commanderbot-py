from typing import Literal, Optional, override

from commanderbot.ext.automod.action import AutomodAction
from commanderbot.ext.automod.automod_context import AutomodContext
from commanderbot.lib.predicates import is_member
from commanderbot.lib.types import Timedelta

__all__ = ("TimeoutAuthor",)


class TimeoutAuthor(AutomodAction):
    """
    Timeout the author in context.
    """

    type: Literal["timeout_author"]

    duration: Timedelta
    """
    How long the timeout will be.
    
    Note that the API only allows for timeouts up to 28 days.
    """

    reason: Optional[str] = None
    """The reason for the timeout, if any."""

    @override
    async def apply(self, context: AutomodContext):
        if (author := context.event.author) and is_member(author):
            await author.timeout(self.duration, reason=self.reason)
