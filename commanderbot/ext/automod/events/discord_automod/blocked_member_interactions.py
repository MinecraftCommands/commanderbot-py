from dataclasses import dataclass
from typing import override

import discord
from discord import Member, User

from commanderbot.ext.automod.event import AutomodEvent
from commanderbot.lib.predicates import is_member, is_user
from commanderbot.lib.types import DiscordAutomodRuleID

__all__ = ("DiscordAutomodBlockedMemberInteractions",)


@dataclass
class DiscordAutomodBlockedMemberInteractions(AutomodEvent):
    _execution: discord.AutoModAction

    @property
    def rule_id(self) -> DiscordAutomodRuleID:
        """The ID of the Discord automod rule."""
        return self._execution.rule_id

    @property
    def matched_content(self) -> str:
        """The matched content from the username/nickname."""
        assert isinstance(self._execution.matched_content, str)
        return self._execution.matched_content

    @property
    def matched_keyword(self) -> str:
        """The keyword the username/nickname matched."""
        assert isinstance(self._execution.matched_keyword, str)
        return self._execution.matched_keyword

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
