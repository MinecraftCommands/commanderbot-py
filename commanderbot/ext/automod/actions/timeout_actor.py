from typing import Literal, Optional, override

from commanderbot.ext.automod.action import AutomodAction
from commanderbot.ext.automod.automod_context import AutomodContext
from commanderbot.lib.predicates import is_member
from commanderbot.lib.types import Timedelta

__all__ = ("TimeoutActor",)


class TimeoutActor(AutomodAction):
    """
    Timeout the actor in context.
    """

    type: Literal["timeout_actor"]

    duration: Timedelta
    """
    How long the timeout will be.
    
    Note that the API only allows for timeouts up to 28 days.
    """

    reason: Optional[str] = None
    """The reason for the timeout, if any."""

    @override
    async def apply(self, context: AutomodContext):
        if (actor := context.event.actor) and is_member(actor):
            await actor.timeout(self.duration, reason=self.reason)
