from typing import Literal

from commanderbot.ext.automod import events
from commanderbot.ext.automod.trigger import AutomodTrigger

__all__ = ("MemberLeft",)


class MemberLeft(AutomodTrigger):
    """
    Triggers when a member leaves the guild.
    """

    type: Literal["member_left"]
    event_types = (events.MemberLeft,)
