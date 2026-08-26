from typing import Literal

from commanderbot.ext.automod import events
from commanderbot.ext.automod.triggers.message import Message

__all__ = ("MessageEdited",)


class MessageEdited(Message):
    """
    Triggers when a message is edited.
    """

    type: Literal["message_edited"]
    event_types = (events.MessageEdited,)
