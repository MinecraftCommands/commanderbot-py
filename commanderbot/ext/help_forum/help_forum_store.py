from dataclasses import dataclass
from typing import Optional

from discord import ForumChannel, ForumTag, Guild

from commanderbot.ext.help_forum.help_forum_data import HelpForum, HelpForumData
from commanderbot.lib.cogs import CogStore
from commanderbot.lib.databases.json_db import JsonDB


@dataclass
class HelpForumStore(CogStore):
    db: JsonDB[HelpForumData]

    async def require_help_forum(self, guild: Guild, forum: ForumChannel) -> HelpForum:
        cache = await self.db.get_cache()
        return cache.require_help_forum(guild, forum)

    async def get_help_forum(
        self, guild: Guild, forum: ForumChannel
    ) -> Optional[HelpForum]:
        cache = await self.db.get_cache()
        return cache.get_help_forum(guild, forum)

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
        help_forum = cache.register_forum_channel(
            guild, forum, unresolved_emoji, resolved_emoji, unresolved_tag, resolved_tag
        )
        await self.db.commit()
        return help_forum

    async def deregister_forum_channel(
        self, guild: Guild, forum: ForumChannel
    ) -> HelpForum:
        cache = await self.db.get_cache()
        help_forum = cache.deregister_forum_channel(guild, forum)
        await self.db.commit()
        return help_forum

    async def increment_threads_created(self, help_forum: HelpForum):
        cache = await self.db.get_cache()
        cache.increment_threads_created(help_forum)
        await self.db.commit()

    async def increment_resolutions(self, help_forum: HelpForum):
        cache = await self.db.get_cache()
        cache.increment_resolutions(help_forum)
        await self.db.commit()

    async def modify_unresolved_emoji(
        self, guild: Guild, forum: ForumChannel, emoji: str
    ) -> HelpForum:
        cache = await self.db.get_cache()
        help_forum = cache.modify_unresolved_emoji(guild, forum, emoji)
        await self.db.commit()
        return help_forum

    async def modify_resolved_emoji(
        self, guild: Guild, forum: ForumChannel, emoji: str
    ) -> HelpForum:
        cache = await self.db.get_cache()
        help_forum = cache.modify_resolved_emoji(guild, forum, emoji)
        await self.db.commit()
        return help_forum

    async def modify_unresolved_tag(
        self, guild: Guild, forum: ForumChannel, tag: str
    ) -> tuple[HelpForum, ForumTag]:
        cache = await self.db.get_cache()
        result = cache.modify_unresolved_tag(guild, forum, tag)
        await self.db.commit()
        return result

    async def modify_resolved_tag(
        self, guild: Guild, forum: ForumChannel, tag: str
    ) -> tuple[HelpForum, ForumTag]:
        cache = await self.db.get_cache()
        result = cache.modify_resolved_tag(guild, forum, tag)
        await self.db.commit()
        return result
