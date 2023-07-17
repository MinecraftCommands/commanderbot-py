import re
from dataclasses import dataclass
from typing import AsyncIterable, Optional, Union

from discord import Guild

from commanderbot.ext.faq.faq_data import FaqData
from commanderbot.ext.faq.faq_store import FaqEntry
from commanderbot.lib import UserID
from commanderbot.lib.cogs import CogStore
from commanderbot.lib.cogs.database import JsonFileDatabaseAdapter


# @implements FaqStore
@dataclass
class FaqJsonStore(CogStore):
    """
    Implementation of `FaqStore` that uses a simple JSON file to persist state.
    """

    db: JsonFileDatabaseAdapter[FaqData]

    # @implements FaqStore
    async def require_faq(self, guild: Guild, key: str) -> FaqEntry:
        cache = await self.db.get_cache()
        return await cache.require_faq(guild, key)

    # @implements FaqStore
    async def require_prefix_pattern(self, guild: Guild) -> re.Pattern:
        cache = await self.db.get_cache()
        return await cache.require_prefix_pattern(guild)

    # @implements FaqStore
    async def require_match_pattern(self, guild: Guild) -> re.Pattern:
        cache = await self.db.get_cache()
        return await cache.require_match_pattern(guild)

    # @implements FaqStore
    async def get_prefix_pattern(self, guild: Guild) -> Optional[re.Pattern]:
        cache = await self.db.get_cache()
        return await cache.get_prefix_pattern(guild)

    # @implements FaqStore
    async def get_match_pattern(self, guild: Guild) -> Optional[re.Pattern]:
        cache = await self.db.get_cache()
        return await cache.get_match_pattern(guild)

    # @implements FaqStore
    async def add_faq(
        self,
        guild: Guild,
        key: str,
        aliases: list[str],
        tags: list[str],
        content: str,
        user_id: UserID,
    ) -> FaqEntry:
        cache = await self.db.get_cache()
        entry = await cache.add_faq(guild, key, aliases, tags, content, user_id)
        await self.db.dirty()
        return entry

    # @implements FaqStore
    async def modify_faq(
        self,
        guild: Guild,
        key: str,
        aliases: list[str],
        tags: list[str],
        content: str,
        user_id: UserID,
    ) -> FaqEntry:
        cache = await self.db.get_cache()
        entry = await cache.modify_faq(guild, key, aliases, tags, content, user_id)
        await self.db.dirty()
        return entry

    # @implements FaqStore
    async def increment_faq_hits(self, entry: FaqEntry):
        cache = await self.db.get_cache()
        await cache.increment_faq_hits(entry)
        await self.db.dirty()

    # @implements FaqStore
    async def remove_faq(self, guild: Guild, key: str) -> FaqEntry:
        cache = await self.db.get_cache()
        entry = await cache.remove_faq(guild, key)
        await self.db.dirty()
        return entry

    # @implements FaqStore
    async def query_faq(self, guild: Guild, query: str) -> Optional[FaqEntry]:
        cache = await self.db.get_cache()
        return await cache.query_faq(guild, query)

    # @implements FaqStore
    async def query_faqs_by_match(
        self,
        guild: Guild,
        content: str,
        *,
        sort: bool = False,
        cap: Optional[int] = None
    ) -> AsyncIterable[FaqEntry]:
        cache = await self.db.get_cache()
        async for entry in cache.query_faqs_by_match(
            guild, content, sort=sort, cap=cap
        ):
            yield entry

    # @implements FaqStore
    async def query_faqs_by_terms(
        self, guild: Guild, query: str, *, sort: bool = False, cap: Optional[int] = None
    ) -> AsyncIterable[FaqEntry]:
        cache = await self.db.get_cache()
        async for entry in cache.query_faqs_by_terms(guild, query, sort=sort, cap=cap):
            yield entry

    # @implements FaqStore
    async def get_faqs(
        self,
        guild: Guild,
        *,
        faq_filter: Optional[str] = None,
        case_sensitive: bool = False,
        sort: bool = False,
        cap: Optional[int] = None
    ) -> AsyncIterable[FaqEntry]:
        cache = await self.db.get_cache()
        async for entry in cache.get_faqs(
            guild,
            faq_filter=faq_filter,
            case_sensitive=case_sensitive,
            sort=sort,
            cap=cap,
        ):
            yield entry

    # @implements FaqStore
    async def get_faqs_and_aliases(
        self,
        guild: Guild,
        *,
        item_filter: Optional[str] = None,
        case_sensitive: bool = False,
        sort: bool = False,
        cap: Optional[int] = None
    ) -> AsyncIterable[Union[FaqEntry, tuple[str, FaqEntry]]]:
        cache = await self.db.get_cache()
        async for item in cache.get_faqs_and_aliases(
            guild,
            item_filter=item_filter,
            case_sensitive=case_sensitive,
            sort=sort,
            cap=cap,
        ):
            yield item

    # @implements FaqStore
    async def set_prefix_pattern(self, guild: Guild, prefix: str) -> re.Pattern:
        cache = await self.db.get_cache()
        pattern = await cache.set_prefix_pattern(guild, prefix)
        await self.db.dirty()
        return pattern

    # @implements FaqStore
    async def clear_prefix_pattern(self, guild: Guild) -> re.Pattern:
        cache = await self.db.get_cache()
        pattern = await cache.clear_prefix_pattern(guild)
        await self.db.dirty()
        return pattern

    # @implements FaqStore
    async def set_match_pattern(self, guild: Guild, match: str) -> re.Pattern:
        cache = await self.db.get_cache()
        pattern = await cache.set_match_pattern(guild, match)
        await self.db.dirty()
        return pattern

    # @implements FaqStore
    async def clear_match_pattern(self, guild: Guild) -> re.Pattern:
        cache = await self.db.get_cache()
        pattern = await cache.clear_match_pattern(guild)
        await self.db.dirty()
        return pattern
