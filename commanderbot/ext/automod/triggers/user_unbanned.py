from typing import Literal

from commanderbot.ext.automod import events
from commanderbot.ext.automod.trigger import AutomodTrigger

__all__ = ("UserUnbanned",)


class UserUnbanned(AutomodTrigger):
    """
    Triggers when a user is unbanned.
    """

    type: Literal["user_unbanned"] = "user_unbanned"
    event_types = (events.UserUnbanned,)
