import math
from collections import defaultdict
from typing import Annotated, Optional

from discord import ForumChannel, ForumTag, Guild, PartialEmoji
from pydantic import BaseModel, Field

from commanderbot.ext.help_forum.help_forum_exceptions import (
    ForumChannelAlreadyRegistered,
    ForumChannelNotRegistered,
    HelpForumInvalidTag,
)
from commanderbot.lib import ChannelID, ForumTagID, GuildID, utils


class HelpForum(BaseModel):
    channel_id: ChannelID
    unresolved_emoji: str
    resolved_emoji: str
    unresolved_tag_id: ForumTagID
    resolved_tag_id: ForumTagID
    threads_created: int
    resolutions: int

    @property
    def partial_unresolved_emoji(self) -> PartialEmoji:
        return PartialEmoji.from_str(self.unresolved_emoji)

    @property
    def partial_resolved_emoji(self) -> PartialEmoji:
        return PartialEmoji.from_str(self.resolved_emoji)

    @property
    def thread_state_tags(self) -> tuple[ForumTagID, ForumTagID]:
        return (self.unresolved_tag_id, self.resolved_tag_id)

    @property
    def ratio(self) -> tuple[int, int]:
        if self.threads_created == 0 or self.resolutions == 0:
            return (self.threads_created, self.resolutions)

        gcd: int = math.gcd(self.threads_created, self.resolutions)
        return (self.threads_created // gcd, self.resolutions // gcd)


class HelpForumGuildData(BaseModel):
    help_forums: dict[ChannelID, HelpForum] = Field(
        default_factory=dict, exclude_if=lambda v: not v
    )

    def _is_forum_registered(self, forum: ForumChannel):
        return forum.id in self.help_forums

    def _require_tag(self, forum: ForumChannel, tag_str: str) -> ForumTag:
        # Returns the forum tag if it exists
        # This is just a wrapper around our library function so we can throw a custom exception
        try:
            return utils.require_forum_tag(forum, tag_str)
        except:
            raise HelpForumInvalidTag(forum.id, tag_str)

    def require_help_forum(self, forum: ForumChannel) -> HelpForum:
        # Returns the help forum data if it exists
        if forum_data := self.help_forums.get(forum.id):
            return forum_data
        # Otherwise, raise
        raise ForumChannelNotRegistered(forum.id)

    def get_help_forum(self, forum: ForumChannel) -> Optional[HelpForum]:
        return self.help_forums.get(forum.id)

    def register_forum_channel(
        self,
        forum: ForumChannel,
        unresolved_emoji: str,
        resolved_emoji: str,
        unresolved_tag: str,
        resolved_tag: str,
    ) -> HelpForum:
        # Check if the forum channel was already registered
        if self._is_forum_registered(forum):
            raise ForumChannelAlreadyRegistered(forum.id)

        # Check if the tags exist in the forum channel
        valid_unresolved_tag: ForumTag = self._require_tag(forum, unresolved_tag)
        valid_resolved_tag: ForumTag = self._require_tag(forum, resolved_tag)

        # Create and add a new help forum
        forum_data = HelpForum(
            channel_id=forum.id,
            unresolved_emoji=unresolved_emoji,
            resolved_emoji=resolved_emoji,
            unresolved_tag_id=valid_unresolved_tag.id,
            resolved_tag_id=valid_resolved_tag.id,
            threads_created=0,
            resolutions=0,
        )

        self.help_forums[forum.id] = forum_data

        # Return the newly created help forum
        return forum_data

    def deregister_forum_channel(self, forum: ForumChannel) -> HelpForum:
        # The help forum channel should exist
        forum_data = self.require_help_forum(forum)
        # Remove it
        del self.help_forums[forum_data.channel_id]
        # Return it
        return forum_data

    def modify_unresolved_emoji(self, forum: ForumChannel, emoji: str) -> HelpForum:
        # Modify unresolved emoji for a help forum
        forum_data = self.require_help_forum(forum)
        forum_data.unresolved_emoji = emoji
        return forum_data

    def modify_resolved_emoji(self, forum: ForumChannel, emoji: str) -> HelpForum:
        # Modify resolved emoji for a help forum
        forum_data = self.require_help_forum(forum)
        forum_data.resolved_emoji = emoji
        return forum_data

    def modify_unresolved_tag(
        self, forum: ForumChannel, tag: str
    ) -> tuple[HelpForum, ForumTag]:
        # Modify unresolved tag ID for a help forum
        forum_data = self.require_help_forum(forum)
        valid_tag = self._require_tag(forum, tag)
        forum_data.unresolved_tag_id = valid_tag.id
        return (forum_data, valid_tag)

    def modify_resolved_tag(
        self, forum: ForumChannel, tag: str
    ) -> tuple[HelpForum, ForumTag]:
        # Modify resolved tag ID for a help forum
        forum_data = self.require_help_forum(forum)
        valid_tag = self._require_tag(forum, tag)
        forum_data.resolved_tag_id = valid_tag.id
        return (forum_data, valid_tag)


class HelpForumData(BaseModel):
    guilds: defaultdict[
        GuildID,
        Annotated[HelpForumGuildData, Field(default_factory=HelpForumGuildData)],
    ] = Field(
        default_factory=lambda: defaultdict(HelpForumGuildData),
        exclude_if=lambda v: not v,
    )

    def require_help_forum(self, guild: Guild, forum: ForumChannel) -> HelpForum:
        return self.guilds[guild.id].require_help_forum(forum)

    def get_help_forum(
        self, guild: Guild, forum: ForumChannel
    ) -> Optional[HelpForum]:
        return self.guilds[guild.id].get_help_forum(forum)

    def register_forum_channel(
        self,
        guild: Guild,
        forum: ForumChannel,
        unresolved_emoji: str,
        resolved_emoji: str,
        unresolved_tag: str,
        resolved_tag: str,
    ) -> HelpForum:
        return self.guilds[guild.id].register_forum_channel(
            forum, unresolved_emoji, resolved_emoji, unresolved_tag, resolved_tag
        )

    def deregister_forum_channel(
        self, guild: Guild, forum: ForumChannel
    ) -> HelpForum:
        return self.guilds[guild.id].deregister_forum_channel(forum)

    def increment_threads_created(self, help_forum: HelpForum):
        help_forum.threads_created += 1

    def increment_resolutions(self, help_forum: HelpForum):
        help_forum.resolutions += 1

    def modify_unresolved_emoji(
        self, guild: Guild, forum: ForumChannel, emoji: str
    ) -> HelpForum:
        return self.guilds[guild.id].modify_unresolved_emoji(forum, emoji)

    def modify_resolved_emoji(
        self, guild: Guild, forum: ForumChannel, emoji: str
    ) -> HelpForum:
        return self.guilds[guild.id].modify_resolved_emoji(forum, emoji)

    def modify_unresolved_tag(
        self, guild: Guild, forum: ForumChannel, tag: str
    ) -> tuple[HelpForum, ForumTag]:
        return self.guilds[guild.id].modify_unresolved_tag(forum, tag)

    def modify_resolved_tag(
        self, guild: Guild, forum: ForumChannel, tag: str
    ) -> tuple[HelpForum, ForumTag]:
        return self.guilds[guild.id].modify_resolved_tag(forum, tag)
