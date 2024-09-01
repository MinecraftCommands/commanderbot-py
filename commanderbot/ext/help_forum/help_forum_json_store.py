from dataclasses import dataclass
from typing import Optional

from discord import ForumChannel, ForumTag, Guild

from commanderbot.ext.help_forum.help_forum_data import HelpForumData
from commanderbot.ext.help_forum.help_forum_store import HelpForum
from commanderbot.lib.cogs import CogStore
from commanderbot.lib.cogs.database import JsonFileDatabaseAdapter


# @implements HelpForumStore
@dataclass
class HelpForumJsonStore(CogStore):
    """
    Implementation of `HelpForumStore` that uses a simple JSON file to persist state.
    """

    db: JsonFileDatabaseAdapter[HelpForumData]

    # @implements HelpForumStore
    async def require_help_forum(self, guild: Guild, forum: ForumChannel) -> HelpForum:
        cache = await self.db.get_cache()
        return await cache.require_help_forum(guild, forum)

    async def get_help_forum(
        self, guild: Guild, forum: ForumChannel
    ) -> Optional[HelpForum]:
        cache = await self.db.get_cache()
        return await cache.get_help_forum(guild, forum)

    # @implements HelpForumStore
    async def register_forum_channel(
        self,
        guild: Guild,
        forum: ForumChannel,
        unresolved_emoji: str,
        resolved_emoji: str,
        unresolved_tag: str,
        resolved_tag: str,
    ) -> HelpForum:
        cache = await self.db.get_cache()
        help_forum = await cache.register_forum_channel(
            guild, forum, unresolved_emoji, resolved_emoji, unresolved_tag, resolved_tag
        )
        await self.db.dirty()
        return help_forum

    # @implements HelpForumStore
    async def deregister_forum_channel(
        self, guild: Guild, forum: ForumChannel
    ) -> HelpForum:
        cache = await self.db.get_cache()
        help_forum = await cache.deregister_forum_channel(guild, forum)
        await self.db.dirty()
        return help_forum

    # @implements HelpForumStore
    async def increment_threads_created(self, help_forum: HelpForum):
        cache = await self.db.get_cache()
        await cache.increment_threads_created(help_forum)
        await self.db.dirty()

    # @implements HelpForumStore
    async def increment_resolutions(self, help_forum: HelpForum):
        cache = await self.db.get_cache()
        await cache.increment_resolutions(help_forum)
        await self.db.dirty()

    # @implements HelpForumStore
    async def modify_unresolved_emoji(
        self, guild: Guild, forum: ForumChannel, emoji: str
    ) -> HelpForum:
        cache = await self.db.get_cache()
        help_forum = await cache.modify_unresolved_emoji(guild, forum, emoji)
        await self.db.dirty()
        return help_forum

    # @implements HelpForumStore
    async def modify_resolved_emoji(
        self, guild: Guild, forum: ForumChannel, emoji: str
    ) -> HelpForum:
        cache = await self.db.get_cache()
        help_forum = await cache.modify_resolved_emoji(guild, forum, emoji)
        await self.db.dirty()
        return help_forum

    # @implements HelpForumStore
    async def modify_unresolved_tag(
        self, guild: Guild, forum: ForumChannel, tag: str
    ) -> tuple[HelpForum, ForumTag]:
        cache = await self.db.get_cache()
        result = await cache.modify_unresolved_tag(guild, forum, tag)
        await self.db.dirty()
        return result

    # @implements HelpForumStore
    async def modify_resolved_tag(
        self, guild: Guild, forum: ForumChannel, tag: str
    ) -> tuple[HelpForum, ForumTag]:
        cache = await self.db.get_cache()
        result = await cache.modify_resolved_tag(guild, forum, tag)
        await self.db.dirty()
        return result
