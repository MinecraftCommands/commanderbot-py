from typing import Literal

from commanderbot.ext.automod import events
from commanderbot.ext.automod.triggers.message import Message

__all__ = ("MessageSent",)


class MessageSent(Message):
    """
    Triggers when a message is sent.
    """

    type: Literal["message_sent"] = "message_sent"
    event_types = (events.MessageSent,)
