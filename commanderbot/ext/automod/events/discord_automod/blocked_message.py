from dataclasses import dataclass
from typing import override

import discord
from discord import Member, Thread, User

from commanderbot.ext.automod.event import AutomodEvent
from commanderbot.lib.predicates import (
    is_member,
    is_messagable_guild_channel,
    is_thread,
    is_user,
)
from commanderbot.lib.types import DiscordAutomodRuleID, MessageableGuildChannel

__all__ = ("DiscordAutomodBlockedMessage",)


@dataclass
class DiscordAutomodBlockedMessage(AutomodEvent):
    _execution: discord.AutoModAction

    @property
    def rule_id(self) -> DiscordAutomodRuleID:
        """The ID of the Discord automod rule."""
        return self._execution.rule_id

    @property
    def content(self) -> str:
        """The content of the message."""
        return self._execution.content

    @property
    def matched_content(self) -> str:
        """The matched content from the message."""
        assert isinstance(self._execution.matched_content, str)
        return self._execution.matched_content

    @property
    def matched_keyword(self) -> str:
        """The keyword the content matched."""
        assert isinstance(self._execution.matched_keyword, str)
        return self._execution.matched_keyword

    @property
    @override
    def channel(self) -> MessageableGuildChannel | Thread:
        assert is_messagable_guild_channel(self._execution.channel) or is_thread(
            self._execution.channel
        )
        return self._execution.channel

    @property
    @override
    def author(self) -> Member:
        assert is_member(self._execution.member)
        return self._execution.member

    @property
    @override
    def actor(self) -> Member:
        assert is_member(self._execution.member)
        return self._execution.member

    @property
    @override
    def member(self) -> Member:
        assert is_member(self._execution.member)
        return self._execution.member

    @property
    @override
    def user(self) -> User:
        assert is_user(self._execution.member)
        return self._execution.member
