from dataclasses import dataclass
from typing import AsyncIterable, Optional, Union

from discord import Guild

from commanderbot.ext.invite.invite_data import InviteData
from commanderbot.ext.invite.invite_store import InviteEntry
from commanderbot.lib import UserID
from commanderbot.lib.cogs import CogStore
from commanderbot.lib.cogs.database import JsonFileDatabaseAdapter


# @implements InviteStore
@dataclass
class InviteJsonStore(CogStore):
    """
    Implementation of `InviteStore` that uses a simple JSON file to persist state.
    """

    db: JsonFileDatabaseAdapter[InviteData]

    # @implements InviteStore
    async def require_invite(self, guild: Guild, key: str) -> InviteEntry:
        cache = await self.db.get_cache()
        return await cache.require_invite(guild, key)

    # @implements InviteStore
    async def require_guild_invite(self, guild: Guild) -> InviteEntry:
        cache = await self.db.get_cache()
        return await cache.require_guild_invite(guild)

    # @implements InviteStore
    async def add_invite(
        self,
        guild: Guild,
        key: str,
        tags: list[str],
        link: str,
        description: Optional[str],
        user_id: UserID,
    ) -> InviteEntry:
        cache = await self.db.get_cache()
        entry = await cache.add_invite(guild, key, tags, link, description, user_id)
        await self.db.dirty()
        return entry

    # @implements InviteStore
    async def modify_invite(
        self,
        guild: Guild,
        key: str,
        tags: list[str],
        link: str,
        description: Optional[str],
        user_id: UserID,
    ) -> InviteEntry:
        cache = await self.db.get_cache()
        entry = await cache.modify_invite(guild, key, tags, link, description, user_id)
        await self.db.dirty()
        return entry

    # @implements InviteStore
    async def increment_invite_hits(self, entry: InviteEntry):
        cache = await self.db.get_cache()
        await cache.increment_invite_hits(entry)
        await self.db.dirty()

    # @implements InviteStore
    async def remove_invite(self, guild: Guild, key: str) -> InviteEntry:
        cache = await self.db.get_cache()
        entry = await cache.remove_invite(guild, key)
        await self.db.dirty()
        return entry

    # @implements InviteStore
    async def query_invites(
        self, guild: Guild, query: str
    ) -> AsyncIterable[InviteEntry]:
        cache = await self.db.get_cache()
        async for entry in cache.query_invites(guild, query):
            yield entry

    # @implements InviteStore
    async def get_invites(
        self, guild: Guild, *, invite_filter: Optional[str] = None, sort: bool = False
    ) -> AsyncIterable[InviteEntry]:
        cache = await self.db.get_cache()
        async for entry in cache.get_invites(
            guild, invite_filter=invite_filter, sort=sort
        ):
            yield entry

    # @implements InviteStore
    async def get_tags(
        self, guild: Guild, *, tag_filter: Optional[str] = None, sort: bool = False
    ) -> AsyncIterable[str]:
        cache = await self.db.get_cache()
        async for tag in cache.get_tags(guild, tag_filter=tag_filter, sort=sort):
            yield tag

    # @implements InviteStore
    async def get_invites_and_tags(
        self, guild: Guild, *, item_filter: Optional[str] = None, sort: bool = False
    ) -> AsyncIterable[Union[InviteEntry, str]]:
        cache = await self.db.get_cache()
        async for item in cache.get_invites_and_tags(
            guild, item_filter=item_filter, sort=sort
        ):
            yield item

    # @implements InviteStore
    async def set_guild_invite(self, guild: Guild, key: str) -> InviteEntry:
        cache = await self.db.get_cache()
        entry = await cache.set_guild_invite(guild, key)
        await self.db.dirty()
        return entry

    # @implements InviteStore
    async def clear_guild_invite(self, guild: Guild) -> InviteEntry:
        cache = await self.db.get_cache()
        entry = await cache.clear_guild_invite(guild)
        await self.db.dirty()
        return entry
