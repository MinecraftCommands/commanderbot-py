from typing import Literal

from commanderbot.ext.automod import events
from commanderbot.ext.automod.trigger import AutomodTrigger

__all__ = ("MemberBanned",)


class MemberBanned(AutomodTrigger):
    """
    Triggers when a member is banned.
    """

    type: Literal["member_banned"]
    event_types = (events.MemberBanned,)
