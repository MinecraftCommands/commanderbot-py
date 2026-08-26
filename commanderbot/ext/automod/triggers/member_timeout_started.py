from typing import Literal, override

from commanderbot.ext.automod import events
from commanderbot.ext.automod.automod_context import AutomodContext
from commanderbot.ext.automod.trigger import AutomodTrigger

__all__ = ("MemberTimeoutStarted",)


class MemberTimeoutStarted(AutomodTrigger):
    """
    Triggers when a member's timeout starts.
    """

    type: Literal["member_timeout_started"]
    event_types = (events.MemberUpdated,)

    @override
    async def poll(self, context: AutomodContext) -> bool:
        event = context.event
        assert isinstance(event, events.MemberUpdated)

        timeout_before = event.before.is_timed_out()
        timeout_after = event.after.is_timed_out()

        return not timeout_before and timeout_after
