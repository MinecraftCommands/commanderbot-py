from dataclasses import dataclass
from typing import override

from discord import Attachment, Member, Message, Reaction, Thread, User

from commanderbot.ext.automod.event import AutomodEvent
from commanderbot.lib.predicates import is_messagable_guild_channel, is_thread, is_user
from commanderbot.lib.types import MessageableGuildChannel

__all__ = ("ReactionRemoved",)


@dataclass
class ReactionRemoved(AutomodEvent):
    _reaction: Reaction
    _member: Member

    @property
    @override
    def channel(self) -> MessageableGuildChannel | Thread:
        assert is_messagable_guild_channel(self.message.channel) or is_thread(
            self.message.channel
        )
        return self.message.channel

    @property
    @override
    def message(self) -> Message:
        return self.reaction.message

    @property
    @override
    def attachments(self) -> list[Attachment]:
        return self.reaction.message.attachments

    @property
    @override
    def reaction(self) -> Reaction:
        return self._reaction

    @property
    @override
    def author(self) -> Member | User:
        return self.message.author

    @property
    @override
    def actor(self) -> Member:
        return self._member

    @property
    @override
    def member(self) -> Member:
        return self._member

    @property
    @override
    def user(self) -> User:
        assert is_user(self._member)
        return self._member
