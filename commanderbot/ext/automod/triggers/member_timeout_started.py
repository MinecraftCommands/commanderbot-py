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

        timeout_before = event.before.timed_out_until
        timeout_after = event.after.timed_out_until

        if timeout_before is None and timeout_after is not None:
            return True
        return False
