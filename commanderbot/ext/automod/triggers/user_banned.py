from typing import Literal

from commanderbot.ext.automod import events
from commanderbot.ext.automod.trigger import AutomodTrigger

__all__ = ("UserBanned",)


class UserBanned(AutomodTrigger):
    """
    Triggers when a user is banned.
    """

    type: Literal["user_banned"] = "user_banned"
    event_types = (events.UserBanned,)
