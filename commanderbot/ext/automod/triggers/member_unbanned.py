from typing import Literal

from commanderbot.ext.automod import events
from commanderbot.ext.automod.trigger import AutomodTrigger

__all__ = ("MemberUnbanned",)


class MemberUnbanned(AutomodTrigger):
    """
    Triggers when a member is unbanned.
    """

    type: Literal["member_unbanned"]
    event_types = (events.MemberUnbanned,)
