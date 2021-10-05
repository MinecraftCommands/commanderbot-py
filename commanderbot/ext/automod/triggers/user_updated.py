from dataclasses import dataclass
from typing import Any

from commanderbot.ext.automod import events
from commanderbot.ext.automod.trigger import Trigger, TriggerBase


@dataclass
class UserUpdated(TriggerBase):
    """
    Fires when an `on_user_update` event is received.

    This occurs when one or more of the following things change:
    - avatar
    - username
    - discriminator

    See: https://discordpy.readthedocs.io/en/stable/api.html?highlight=events#discord.on_user_update
    """

    event_types = (events.UserUpdated,)


def create_trigger(data: Any) -> Trigger:
    return UserUpdated.from_data(data)
