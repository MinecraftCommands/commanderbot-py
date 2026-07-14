from typing import Literal

from commanderbot.ext.automod import events
from commanderbot.ext.automod.triggers.message import Message

__all__ = ("MessageDeleted",)


class MessageDeleted(Message):
    """
    Triggers when a message is deleted.
    """

    type: Literal["message_deleted"]
    event_types = (events.MessageDeleted,)
