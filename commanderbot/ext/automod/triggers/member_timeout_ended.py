from typing import Literal, override

from commanderbot.ext.automod import events
from commanderbot.ext.automod.automod_context import AutomodContext
from commanderbot.ext.automod.trigger import AutomodTrigger

__all__ = ("MemberTimeoutEnded",)


class MemberTimeoutEnded(AutomodTrigger):
    """
    Triggers when a member's timeout ends.

    Due to a Discord limitation, this will not trigger when a member's timeout expires.
    """

    type: Literal["member_timeout_ended"]
    event_types = (events.MemberUpdated,)

    @override
    async def poll(self, context: AutomodContext) -> bool:
        event = context.event
        assert isinstance(event, events.MemberUpdated)

        timeout_before = event.before.is_timed_out()
        timeout_after = event.after.is_timed_out()

        return timeout_before and not timeout_after
