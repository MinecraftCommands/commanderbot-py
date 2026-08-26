from typing import Literal

from commanderbot.ext.automod import events
from commanderbot.ext.automod.trigger import AutomodTrigger

__all__ = ("MemberJoined",)


class MemberJoined(AutomodTrigger):
    """
    Triggers when a member joins the guild.
    """

    type: Literal["member_joined"]
    event_types = (events.MemberJoined,)
