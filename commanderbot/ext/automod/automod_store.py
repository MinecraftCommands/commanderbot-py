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

    async def require_default_log(
        self,
        guild: Guild,
    ) -> LogChannel:
        cache = await self.db.get_cache()
        guild_data = cache.guilds[guild.id]
        return guild_data.require_default_log()

    async def get_default_log(
        self,
        guild: Guild,
    ) -> Optional[LogChannel]:
        cache = await self.db.get_cache()
        guild_data = cache.guilds[guild.id]
        return guild_data.get_default_log()

    async def set_default_log(self, guild: Guild, log: LogChannel) -> LogChannel:
        cache = await self.db.get_cache()
        guild_data = cache.guilds[guild.id]
        result = guild_data.set_default_log(log)
        await self.db.commit()
        return result

    async def modify_default_log(
        self, guild: Guild, log: LogChannel
    ) -> tuple[LogChannel, LogChannel]:
        cache = await self.db.get_cache()
        guild_data = cache.guilds[guild.id]
        result = guild_data.modify_default_log(log)
        await self.db.commit()
        return result

    async def remove_default_log(
        self,
        guild: Guild,
    ) -> LogChannel:
        cache = await self.db.get_cache()
        guild_data = cache.guilds[guild.id]
        result = guild_data.remove_default_log()
        await self.db.commit()
        return result

    async def require_rule(self, guild: Guild, name: str) -> AutomodRule:
        cache = await self.db.get_cache()
        guild_data = cache.guilds[guild.id]
        return guild_data.require_rule(name)

    async def require_rule_metadata(
        self, guild: Guild, name: str
    ) -> AutomodRuleMetadata:
        cache = await self.db.get_cache()
        guild_data = cache.guilds[guild.id]
        return guild_data.require_rule_metadata(name)

    async def has_rule(self, guild: Guild, name: str) -> bool:
        cache = await self.db.get_cache()
        guild_data = cache.guilds[guild.id]
        return guild_data.has_rule(name)

    async def rules_for_event(
        self, guild: Guild, event: AutomodEvent
    ) -> AsyncIterable[AutomodRule]:
        cache = await self.db.get_cache()
        guild_data = cache.guilds[guild.id]
        for rule in guild_data.rules_for_event(event):
            yield rule

    async def add_rule(
        self, guild: Guild, rule: AutomodRule, user_id: UserID
    ) -> tuple[AutomodRule, AutomodRuleMetadata]:
        cache = await self.db.get_cache()
        guild_data = cache.guilds[guild.id]
        result = guild_data.add_rule(rule, user_id)
        await self.db.commit()
        return result

    async def modify_rule(
        self, guild: Guild, rule: AutomodRule, user_id: UserID
    ) -> tuple[AutomodRule, AutomodRule, AutomodRuleMetadata]:
        cache = await self.db.get_cache()
        guild_data = cache.guilds[guild.id]
        result = guild_data.modify_rule(rule, user_id)
        await self.db.commit()
        return result

    async def remove_rule(
        self, guild: Guild, name: str
    ) -> tuple[AutomodRule, AutomodRuleMetadata]:
        cache = await self.db.get_cache()
        guild_data = cache.guilds[guild.id]
        result = guild_data.remove_rule(name)
        await self.db.commit()
        return result

    async def increment_rule_hits(self, guild: Guild, name: str):
        cache = await self.db.get_cache()
        guild_data = cache.guilds[guild.id]
        guild_data.increment_rule_hits(name)
        await self.db.commit()

    async def yield_rules(
        self, guild: Guild, *, sort: bool = True
    ) -> AsyncIterable[AutomodRule]:
        cache = await self.db.get_cache()
        guild_data = cache.guilds[guild.id]
        for rule in guild_data.yield_rules(sort=sort):
            yield rule

    async def rule_count(self, guild: Guild) -> int:
        cache = await self.db.get_cache()
        guild_data = cache.guilds[guild.id]
        return guild_data.rule_count()

    async def enable_rule(self, guild: Guild, name: str) -> AutomodRule:
        cache = await self.db.get_cache()
        guild_data = cache.guilds[guild.id]
        rule = guild_data.enable_rule(name)
        await self.db.commit()
        return rule

    async def disable_rule(self, guild: Guild, name: str) -> AutomodRule:
        cache = await self.db.get_cache()
        guild_data = cache.guilds[guild.id]
        rule = guild_data.disable_rule(name)
        await self.db.commit()
        return rule

    async def enable_all_rules(self, guild: Guild):
        cache = await self.db.get_cache()
        guild_data = cache.guilds[guild.id]
        guild_data.enable_all_rules()
        await self.db.commit()

    async def disable_all_rules(self, guild: Guild):
        cache = await self.db.get_cache()
        guild_data = cache.guilds[guild.id]
        guild_data.disable_all_rules()
        await self.db.commit()

    async def require_bucket(self, guild: Guild, name: str) -> AutomodBucket:
        cache = await self.db.get_cache()
        guild_data = cache.guilds[guild.id]
        return guild_data.require_bucket(name)

    async def require_bucket_with_type[BucketType = AutomodBucket](
        self, guild: Guild, name: str, bucket_type: type[BucketType]
    ) -> BucketType:
        cache = await self.db.get_cache()
        guild_data = cache.guilds[guild.id]
        return guild_data.require_bucket_with_type(name, bucket_type)

    async def add_bucket(self, guild: Guild, bucket: AutomodBucket) -> AutomodBucket:
        cache = await self.db.get_cache()
        guild_data = cache.guilds[guild.id]
        result = guild_data.add_bucket(bucket)
        await self.db.commit()
        return result

    async def modify_bucket(
        self, guild: Guild, bucket: AutomodBucket
    ) -> tuple[AutomodBucket, AutomodBucket]:
        cache = await self.db.get_cache()
        guild_data = cache.guilds[guild.id]
        result = guild_data.modify_bucket(bucket)
        await self.db.commit()
        return result

    async def remove_bucket(self, guild: Guild, name: str) -> AutomodBucket:
        cache = await self.db.get_cache()
        guild_data = cache.guilds[guild.id]
        bucket = guild_data.remove_bucket(name)
        await self.db.commit()
        return bucket

    async def clear_bucket(self, guild: Guild, name: str) -> AutomodBucket:
        cache = await self.db.get_cache()
        guild_data = cache.guilds[guild.id]
        bucket = guild_data.require_bucket(name)
        await bucket.clear()
        await self.db.commit()
        return bucket

    async def yield_buckets(
        self, guild: Guild, *, sort: bool = True
    ) -> AsyncIterable[AutomodBucket]:
        cache = await self.db.get_cache()
        guild_data = cache.guilds[guild.id]
        for bucket in guild_data.yield_buckets(sort=sort):
            yield bucket

    async def bucket_count(self, guild: Guild) -> int:
        cache = await self.db.get_cache()
        guild_data = cache.guilds[guild.id]
        return guild_data.bucket_count()

    async def enable_bucket(self, guild: Guild, name: str) -> AutomodBucket:
        cache = await self.db.get_cache()
        guild_data = cache.guilds[guild.id]
        bucket = guild_data.enable_bucket(name)
        await self.db.commit()
        return bucket

    async def disable_bucket(self, guild: Guild, name: str) -> AutomodBucket:
        cache = await self.db.get_cache()
        guild_data = cache.guilds[guild.id]
        bucket = guild_data.disable_bucket(name)
        await self.db.commit()
        return bucket

    async def clear_all_buckets(self, guild: Guild):
        cache = await self.db.get_cache()
        guild_data = cache.guilds[guild.id]
        for bucket in guild_data.yield_buckets(sort=False):
            await bucket.clear()
        await self.db.commit()

    async def enable_all_buckets(self, guild: Guild):
        cache = await self.db.get_cache()
        guild_data = cache.guilds[guild.id]
        guild_data.enable_all_buckets()
        await self.db.commit()

    async def disable_all_buckets(self, guild: Guild):
        cache = await self.db.get_cache()
        guild_data = cache.guilds[guild.id]
        guild_data.disable_all_buckets()
        await self.db.commit()
