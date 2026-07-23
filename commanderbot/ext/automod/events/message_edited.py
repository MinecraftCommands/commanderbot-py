from dataclasses import dataclass
from typing import Optional, override

from discord import Attachment, Member, Message, Thread, User

from commanderbot.ext.automod.event import AutomodEvent
from commanderbot.lib.predicates import (
    is_member,
    is_messagable_guild_channel,
    is_thread,
    is_user,
)
from commanderbot.lib.types import MessageableGuildChannel

__all__ = ("MessageEdited",)


@dataclass
class MessageEdited(AutomodEvent):
    before: Message
    """The previous version of the message."""

    after: Message
    """The current version of the message."""

    @property
    @override
    def channel(self) -> MessageableGuildChannel | Thread:
        assert is_messagable_guild_channel(self.after.channel) or is_thread(
            self.after.channel
        )
        return self.after.channel

    @property
    @override
    def message(self) -> Message:
        return self.after

    @property
    @override
    def attachments(self) -> list[Attachment]:
        return self.after.attachments

    @property
    @override
    def author(self) -> Member:
        assert is_member(self.after.author)
        return self.after.author

    @property
    @override
    def actor(self) -> Member:
        assert is_member(self.after.author)
        return self.after.author

    @property
    @override
    def member(self) -> Member:
        assert is_member(self.after.author)
        return self.after.author

    @property
    @override
    def user(self) -> Optional[User]:
        assert is_user(self.after.author)
        return self.after.author
