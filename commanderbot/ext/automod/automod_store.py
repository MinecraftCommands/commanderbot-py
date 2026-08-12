from collections.abc import AsyncIterable
from dataclasses import dataclass
from typing import Optional

from discord import Guild

from commanderbot.ext.automod.automod_data import AutomodData
from commanderbot.ext.automod.bucket import AutomodBucket
from commanderbot.ext.automod.event import AutomodEvent
from commanderbot.ext.automod.rule import AutomodRule, AutomodRuleMetadata
from commanderbot.lib.cogs import CogStore
from commanderbot.lib.databases.json_db import JsonDB
from commanderbot.lib.log_channel import LogChannel
from commanderbot.lib.types import UserID


@dataclass
class AutomodStore(CogStore):
    db: JsonDB[AutomodData]

    async def require_default_log_channel(
        self,
        guild: Guild,
    ) -> LogChannel:
        cache = await self.db.get_cache()
        return cache.require_default_log_channel(guild)

    async def get_default_log_channel(
        self,
        guild: Guild,
    ) -> Optional[LogChannel]:
        cache = await self.db.get_cache()
        return cache.get_default_log_channel(guild)

    async def set_default_log_channel(
        self, guild: Guild, log_channel: LogChannel
    ) -> LogChannel:
        cache = await self.db.get_cache()
        result = cache.set_default_log_channel(guild, log_channel)
        await self.db.commit()
        return result

    async def modify_default_log_channel(
        self, guild: Guild, log_channel: LogChannel
    ) -> tuple[LogChannel, LogChannel]:
        cache = await self.db.get_cache()
        result = cache.modify_default_log_channel(guild, log_channel)
        await self.db.commit()
        return result

    async def remove_default_log_channel(
        self,
        guild: Guild,
    ) -> LogChannel:
        cache = await self.db.get_cache()
        result = cache.remove_default_log_channel(guild)
        await self.db.commit()
        return result

    async def require_rule(self, guild: Guild, name: str) -> AutomodRule:
        cache = await self.db.get_cache()
        return cache.require_rule(guild, name)

    async def require_rule_metadata(
        self, guild: Guild, name: str
    ) -> AutomodRuleMetadata:
        cache = await self.db.get_cache()
        return cache.require_rule_metadata(guild, name)

    async def has_rule(self, guild: Guild, name: str) -> bool:
        cache = await self.db.get_cache()
        return cache.has_rule(guild, name)

    async def rules_for_event(
        self, guild: Guild, event: AutomodEvent
    ) -> AsyncIterable[AutomodRule]:
        cache = await self.db.get_cache()
        for rule in cache.rules_for_event(guild, event):
            yield rule

    async def add_rule(
        self, guild: Guild, rule: AutomodRule, user_id: UserID
    ) -> tuple[AutomodRule, AutomodRuleMetadata]:
        cache = await self.db.get_cache()
        result = cache.add_rule(guild, rule, user_id)
        await self.db.commit()
        return result

    async def modify_rule(
        self, guild: Guild, rule: AutomodRule, user_id: UserID
    ) -> tuple[AutomodRule, AutomodRule, AutomodRuleMetadata]:
        cache = await self.db.get_cache()
        result = cache.modify_rule(guild, rule, user_id)
        await self.db.commit()
        return result

    async def remove_rule(
        self, guild: Guild, name: str
    ) -> tuple[AutomodRule, AutomodRuleMetadata]:
        cache = await self.db.get_cache()
        result = cache.remove_rule(guild, name)
        await self.db.commit()
        return result

    async def increment_rule_hits(self, guild: Guild, name: str):
        cache = await self.db.get_cache()
        cache.increment_rule_hits(guild, name)
        await self.db.commit()

    async def yield_rules(
        self, guild: Guild, *, sort: bool = True
    ) -> AsyncIterable[AutomodRule]:
        cache = await self.db.get_cache()
        for rule in cache.yield_rules(guild, sort):
            yield rule

    async def rule_count(self, guild: Guild) -> int:
        cache = await self.db.get_cache()
        return cache.rule_count(guild)

    async def enable_rule(self, guild: Guild, name: str) -> AutomodRule:
        cache = await self.db.get_cache()
        rule = cache.enable_rule(guild, name)
        await self.db.commit()
        return rule

    async def disable_rule(self, guild: Guild, name: str) -> AutomodRule:
        cache = await self.db.get_cache()
        rule = cache.disable_rule(guild, name)
        await self.db.commit()
        return rule

    async def enable_all_rules(self, guild: Guild):
        cache = await self.db.get_cache()
        cache.enable_all_rules(guild)
        await self.db.commit()

    async def disable_all_rules(self, guild: Guild):
        cache = await self.db.get_cache()
        cache.disable_all_rules(guild)
        await self.db.commit()

    async def require_bucket(self, guild: Guild, name: str) -> AutomodBucket:
        cache = await self.db.get_cache()
        return cache.require_bucket(guild, name)

    async def require_bucket_with_type[BucketType = AutomodBucket](
        self, guild: Guild, name: str, bucket_type: type[BucketType]
    ) -> BucketType:
        cache = await self.db.get_cache()
        return cache.require_bucket_with_type(guild, name, bucket_type)

    async def clear_bucket(self, guild: Guild, name: str):
        cache = await self.db.get_cache()
        bucket = cache.require_bucket(guild, name)
        await bucket.clear()
        await self.db.commit()

    async def bucket_count(self, guild: Guild) -> int:
        cache = await self.db.get_cache()
        return cache.bucket_count(guild)

    async def enable_bucket(self, guild: Guild, name: str) -> AutomodBucket:
        cache = await self.db.get_cache()
        bucket = cache.enable_bucket(guild, name)
        await self.db.commit()
        return bucket

    async def disable_bucket(self, guild: Guild, name: str) -> AutomodBucket:
        cache = await self.db.get_cache()
        bucket = cache.disable_bucket(guild, name)
        await self.db.commit()
        return bucket

    async def enable_all_buckets(self, guild: Guild):
        cache = await self.db.get_cache()
        cache.enable_all_buckets(guild)
        await self.db.commit()

    async def disable_all_buckets(self, guild: Guild):
        cache = await self.db.get_cache()
        cache.disable_all_buckets(guild)
        await self.db.commit()
