from typing import Literal, override

from commanderbot.ext.automod import events
from commanderbot.ext.automod.automod_context import AutomodContext
from commanderbot.ext.automod.trigger import AutomodTrigger

__all__ = ("MemberTimeoutEnded",)


class MemberTimeoutEnded(AutomodTrigger):
    """
    Triggers when a member's timeout ends.
    """

    type: Literal["member_timeout_ended"]
    event_types = (events.MemberUpdated,)

    @override
    async def poll(self, context: AutomodContext) -> bool:
        event = context.event
        assert isinstance(event, events.MemberUpdated)

        timeout_before = event.before.timed_out_until
        timeout_after = event.after.timed_out_until

        if timeout_before is not None and timeout_after is None:
            return True
        return False
