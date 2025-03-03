import re
from dataclasses import dataclass
from typing import AsyncIterable, Optional

from discord import Guild

from commanderbot.ext.friday.friday_data import FridayData
from commanderbot.ext.friday.friday_store import FridayRule
from commanderbot.lib import UserID
from commanderbot.lib.cogs import CogStore
from commanderbot.lib.cogs.database import JsonFileDatabaseAdapter


# @implements FridayStore
@dataclass
class FridayJsonStore(CogStore):
    """
    Implementation of `FridayStore` that uses a simple JSON file to persist state.
    """

    db: JsonFileDatabaseAdapter[FridayData]

    # @implements FridayStore
    async def require_rule(self, guild: Guild, name: str) -> FridayRule:
        cache = await self.db.get_cache()
        return await cache.require_rule(guild, name)

    # @implements FridayStore
    async def add_rule(
        self,
        guild: Guild,
        name: str,
        pattern: Optional[re.Pattern],
        chance: float,
        cooldown: int,
        response: str,
        user_id: UserID,
    ) -> FridayRule:
        cache = await self.db.get_cache()
        rule = await cache.add_rule(
            guild, name, pattern, chance, cooldown, response, user_id
        )
        await self.db.dirty()
        return rule

    # @implements FridayStore
    async def modify_rule(
        self,
        guild: Guild,
        name: str,
        pattern: Optional[re.Pattern],
        chance: float,
        cooldown: int,
        response: str,
        user_id: UserID,
    ) -> FridayRule:
        cache = await self.db.get_cache()
        rule = await cache.modify_rule(
            guild, name, pattern, chance, cooldown, response, user_id
        )
        await self.db.dirty()
        return rule

    # @implements FridayStore
    async def update_on_rule_matched(self, rule: FridayRule):
        cache = await self.db.get_cache()
        await cache.update_on_rule_matched(rule)
        await self.db.dirty()

    # @implements FridayStore
    async def remove_rule(self, guild: Guild, name: str) -> FridayRule:
        cache = await self.db.get_cache()
        rule = await cache.remove_rule(guild, name)
        await self.db.dirty()
        return rule

    # @implements FridayStore
    async def check_rules(self, guild: Guild, content: str) -> Optional[FridayRule]:
        cache = await self.db.get_cache()
        return await cache.check_rules(guild, content)

    # @implements FridayStore
    async def enable(self, guild: Guild):
        cache = await self.db.get_cache()
        await cache.enable(guild)
        await self.db.dirty()

    # @implements FridayStore
    async def disable(self, guild: Guild):
        cache = await self.db.get_cache()
        await cache.disable(guild)
        await self.db.dirty()
