from collections import defaultdict
from collections.abc import Iterable
from typing import Annotated, Any, Optional

from discord import Guild
from discord.utils import utcnow
from pydantic import BaseModel, Field, PrivateAttr

from commanderbot.ext.automod.automod_exceptions import (
    AutomodBucketAlreadyDisabled,
    AutomodBucketAlreadyEnabled,
    AutomodBucketDoesNotExist,
    AutomodRuleAlreadyDisabled,
    AutomodRuleAlreadyEnabled,
    AutomodRuleAlreadyExists,
    AutomodRuleDoesNotExist,
    AutomodRuleMetadataAlreadyExists,
    AutomodRuleMetadataDoesNotExist,
    DefaultLogChannelNotConfigured,
)
from commanderbot.ext.automod.bucket import AutomodBucket
from commanderbot.ext.automod.bucket.types import AutomodBucketType
from commanderbot.ext.automod.event import AutomodEvent
from commanderbot.ext.automod.rule import AutomodRule, AutomodRuleMetadata
from commanderbot.lib.log_channel import LogChannel
from commanderbot.lib.types import GuildID, UserID


class AutomodGuildData(BaseModel):
    default_log: Optional[LogChannel] = None
    rules: dict[str, AutomodRule] = Field(
        default_factory=dict, exclude_if=lambda v: not v
    )
    rule_metadata: dict[str, AutomodRuleMetadata] = Field(
        default_factory=dict, exclude_if=lambda v: not v
    )
    buckets: dict[str, AutomodBucketType] = Field(
        default_factory=dict, exclude_if=lambda v: not v
    )

    _rules_by_event_type: defaultdict[type[AutomodEvent], set[AutomodRule]] = (
        PrivateAttr(default_factory=lambda: defaultdict(set))
    )

    def model_post_init(self, context: Any) -> None:
        self._rebuild_mappings()

    def _rebuild_mappings(self):
        self._rules_by_event_type.clear()
        for rule in self.rules.values():
            for trigger in rule.triggers:
                for event_type in trigger.event_types:
                    self._rules_by_event_type[event_type].add(rule)

    def require_default_log_channel(
        self,
    ) -> LogChannel:
        if log_channel := self.default_log:
            return log_channel
        raise DefaultLogChannelNotConfigured

    def get_default_log_channel(
        self,
    ) -> Optional[LogChannel]:
        return self.default_log

    def set_default_log_channel(self, log_channel: LogChannel) -> LogChannel:
        self.default_log = log_channel
        return self.default_log

    def modify_default_log_channel(
        self, log_channel: LogChannel
    ) -> tuple[LogChannel, LogChannel]:
        old_log_channel = self.require_default_log_channel()
        self.default_log = log_channel
        return (old_log_channel, self.default_log)

    def remove_default_log_channel(
        self,
    ) -> LogChannel:
        old_log_channel = self.require_default_log_channel()
        self.default_log = None
        return old_log_channel

    def require_rule(self, name: str) -> AutomodRule:
        if rule := self.rules.get(name):
            return rule
        raise AutomodRuleDoesNotExist(name)

    def require_rule_metadata(self, name: str) -> AutomodRuleMetadata:
        if metadata := self.rule_metadata.get(name):
            return metadata
        raise AutomodRuleMetadataDoesNotExist(name)

    def rules_for_event(self, event: AutomodEvent) -> Iterable[AutomodRule]:
        event_type = type(event)
        if rules := self._rules_by_event_type.get(event_type):
            yield from rules

    def add_rule(
        self, rule: AutomodRule, user_id: UserID
    ) -> tuple[AutomodRule, AutomodRuleMetadata]:
        # The rule name needs to be available
        if rule.name in self.rules:
            raise AutomodRuleAlreadyExists(rule.name)

        # The rule name needs to be available for metadata
        if rule.name in self.rule_metadata:
            raise AutomodRuleMetadataAlreadyExists(rule.name)

        # Create metadata
        metadata = AutomodRuleMetadata(
            name=rule.name,
            hits=0,
            added_by_id=user_id,
            modified_by_id=user_id,
            added_on=utcnow(),
            modified_on=utcnow(),
        )

        # Add rule
        self.rules[rule.name] = rule
        self.rule_metadata[rule.name] = metadata

        self._rebuild_mappings()
        return (rule, metadata)

    def modify_rule(
        self, rule: AutomodRule, user_id: UserID
    ) -> tuple[AutomodRule, AutomodRule, AutomodRuleMetadata]:
        # The rule and metadata need to exist
        old_rule = self.require_rule(rule.name)
        metadata = self.require_rule_metadata(rule.name)

        # Replace the old rule with the modified rule
        self.rules[rule.name] = rule

        # Update metadata
        metadata.modified_by_id = user_id
        metadata.modified_on = utcnow()

        self._rebuild_mappings()
        return (old_rule, rule, metadata)

    def remove_rule(self, name: str) -> tuple[AutomodRule, AutomodRuleMetadata]:
        # The rule and metadata need to exist
        rule = self.require_rule(name)
        metadata = self.require_rule_metadata(name)

        # Delete rule and metadata
        del self.rules[rule.name]
        del self.rule_metadata[rule.name]

        self._rebuild_mappings()
        return (rule, metadata)

    def rule_count(self) -> int:
        return len(self.rules)

    def enable_rule(self, name: str) -> AutomodRule:
        rule = self.require_rule(name)
        if rule.disabled:
            rule.disabled = False
            return rule
        raise AutomodRuleAlreadyEnabled(name)

    def disable_rule(self, name: str) -> AutomodRule:
        rule = self.require_rule(name)
        if not rule.disabled:
            rule.disabled = True
            return rule
        raise AutomodRuleAlreadyDisabled(name)

    def enable_all_rules(self):
        for rule in self.rules.values():
            rule.disabled = False

    def disable_all_rules(self):
        for rule in self.rules.values():
            rule.disabled = True

    def require_bucket(self, name: str) -> AutomodBucket:
        if bucket := self.buckets.get(name):
            return bucket
        raise AutomodBucketDoesNotExist(name)

    def require_bucket_with_type[BucketType = AutomodBucket](
        self, name: str, bucket_type: type[BucketType]
    ) -> BucketType:
        if bucket := self.buckets.get(name):
            if isinstance(bucket, bucket_type):
                return bucket
        raise AutomodBucketDoesNotExist(name)

    def bucket_count(self) -> int:
        return len(self.buckets)

    def enable_bucket(self, name: str):
        bucket = self.require_bucket(name)
        if bucket.disabled:
            bucket.disabled = False
            return bucket
        raise AutomodBucketAlreadyEnabled(name)

    def disable_bucket(self, name: str):
        bucket = self.require_bucket(name)
        if not bucket.disabled:
            bucket.disabled = True
            return bucket
        raise AutomodBucketAlreadyDisabled(name)

    def enable_all_buckets(self):
        for bucket in self.buckets.values():
            bucket.disabled = False

    def disable_all_buckets(self):
        for bucket in self.buckets.values():
            bucket.disabled = True


class AutomodData(BaseModel):
    guilds: defaultdict[
        GuildID,
        Annotated[AutomodGuildData, Field(default_factory=AutomodGuildData)],
    ] = Field(
        default_factory=lambda: defaultdict(AutomodGuildData),
        exclude_if=lambda v: not v,
    )

    def require_default_log_channel(
        self,
        guild: Guild,
    ) -> LogChannel:
        return self.guilds[guild.id].remove_default_log_channel()

    def get_default_log_channel(
        self,
        guild: Guild,
    ) -> Optional[LogChannel]:
        return self.guilds[guild.id].get_default_log_channel()

    def set_default_log_channel(
        self, guild: Guild, log_channel: LogChannel
    ) -> LogChannel:
        return self.guilds[guild.id].set_default_log_channel(log_channel)

    def modify_default_log_channel(
        self, guild: Guild, log_channel: LogChannel
    ) -> tuple[LogChannel, LogChannel]:
        return self.guilds[guild.id].modify_default_log_channel(log_channel)

    def remove_default_log_channel(
        self,
        guild: Guild,
    ) -> LogChannel:
        return self.guilds[guild.id].remove_default_log_channel()

    def require_rule(self, guild: Guild, name: str) -> AutomodRule:
        return self.guilds[guild.id].require_rule(name)

    def require_rule_metadata(self, guild: Guild, name: str) -> AutomodRuleMetadata:
        return self.guilds[guild.id].require_rule_metadata(name)

    def has_rule(self, guild: Guild, name: str) -> bool:
        return name in self.guilds[guild.id].rules

    def rules_for_event(
        self, guild: Guild, event: AutomodEvent
    ) -> Iterable[AutomodRule]:
        yield from self.guilds[guild.id].rules_for_event(event)

    def add_rule(
        self, guild: Guild, rule: AutomodRule, user_id: UserID
    ) -> tuple[AutomodRule, AutomodRuleMetadata]:
        return self.guilds[guild.id].add_rule(rule, user_id)

    def modify_rule(
        self, guild: Guild, rule: AutomodRule, user_id: UserID
    ) -> tuple[AutomodRule, AutomodRule, AutomodRuleMetadata]:
        return self.guilds[guild.id].modify_rule(rule, user_id)

    def remove_rule(
        self, guild: Guild, name: str
    ) -> tuple[AutomodRule, AutomodRuleMetadata]:
        return self.guilds[guild.id].remove_rule(name)

    def increment_rule_hits(self, guild: Guild, name: str):
        metadata = self.guilds[guild.id].require_rule_metadata(name)
        metadata.hits += 1

    def yield_rules(self, guild: Guild, sort: bool) -> Iterable[AutomodRule]:
        rules = self.guilds[guild.id].rules.values()
        yield from sorted(rules, key=lambda rule: rule.name) if sort else rules

    def rule_count(self, guild: Guild) -> int:
        return self.guilds[guild.id].rule_count()

    def enable_rule(self, guild: Guild, name: str) -> AutomodRule:
        return self.guilds[guild.id].enable_rule(name)

    def disable_rule(self, guild: Guild, name: str) -> AutomodRule:
        return self.guilds[guild.id].disable_rule(name)

    def enable_all_rules(self, guild: Guild):
        self.guilds[guild.id].enable_all_rules()

    def disable_all_rules(self, guild: Guild):
        self.guilds[guild.id].disable_all_rules()

    def require_bucket(self, guild: Guild, name: str) -> AutomodBucket:
        return self.guilds[guild.id].require_bucket(name)

    def require_bucket_with_type[BucketType = AutomodBucket](
        self, guild: Guild, name: str, bucket_type: type[BucketType]
    ) -> BucketType:
        return self.guilds[guild.id].require_bucket_with_type(name, bucket_type)

    def bucket_count(self, guild: Guild) -> int:
        return self.guilds[guild.id].bucket_count()

    def enable_bucket(self, guild: Guild, name: str) -> AutomodBucket:
        return self.guilds[guild.id].enable_bucket(name)

    def disable_bucket(self, guild: Guild, name: str) -> AutomodBucket:
        return self.guilds[guild.id].disable_bucket(name)

    def enable_all_buckets(self, guild: Guild):
        self.guilds[guild.id].enable_all_buckets()

    def disable_all_buckets(self, guild: Guild):
        self.guilds[guild.id].disable_all_buckets()
