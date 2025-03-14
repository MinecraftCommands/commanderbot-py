import random
import re
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from itertools import islice
from typing import Any, AsyncIterable, Iterable, Optional, Self

from discord import Guild
from discord.utils import utcnow

from commanderbot.ext.friday.friday_exceptions import (
    ChannelAlreadyRegistered,
    ChannelNotRegistered,
    RuleAlreadyExists,
    RuleDoesNotExist,
)
from commanderbot.ext.friday.friday_store import FridayRule
from commanderbot.lib import (
    ChannelID,
    FromDataMixin,
    GuildID,
    JsonSerializable,
    UserID,
    utils,
)


# @implements FridayRule
@dataclass
class FridayRuleData(JsonSerializable, FromDataMixin):
    name: str
    pattern: Optional[re.Pattern]
    chance: float
    cooldown: int
    response: str
    last_response: Optional[datetime]
    hits: int
    added_by_id: UserID
    modified_by_id: UserID
    added_on: datetime
    modified_on: datetime

    # @implements FromDataMixin
    @classmethod
    def try_from_data(cls, data: Any) -> Optional[Self]:
        if isinstance(data, dict):
            pattern: Optional[re.Pattern] = None
            if raw_pattern := data.get("pattern"):
                pattern = re.compile(raw_pattern, re.IGNORECASE)

            last_response: Optional[datetime] = None
            if raw_last_response := data.get("last_response"):
                last_response = datetime.fromisoformat(raw_last_response)

            return cls(
                name=data["name"],
                pattern=pattern,
                chance=data["chance"],
                cooldown=data["cooldown"],
                response=data["response"],
                last_response=last_response,
                hits=data["hits"],
                added_by_id=data["added_by_id"],
                modified_by_id=data["modified_by_id"],
                added_on=datetime.fromisoformat(data["added_on"]),
                modified_on=datetime.fromisoformat(data["modified_on"]),
            )

    # @implements JsonSerializable
    def to_json(self) -> Any:
        return {
            "name": self.name,
            "pattern": self.pattern.pattern if self.pattern else None,
            "chance": self.chance,
            "cooldown": self.cooldown,
            "response": self.response,
            "last_response": (
                self.last_response.isoformat() if self.last_response else None
            ),
            "hits": self.hits,
            "added_by_id": self.added_by_id,
            "modified_by_id": self.modified_by_id,
            "added_on": self.added_on.isoformat(),
            "modified_on": self.modified_on.isoformat(),
        }

    # @implements FridayRule
    @property
    def available(self) -> bool:
        # Return early if the rule doesn't have a last response
        if not self.last_response:
            return True

        # Get the difference between now and the last response
        now = utcnow()
        delta = now - self.last_response

        # Check if the difference is larger than the cooldown
        cooldown_td = timedelta(seconds=self.cooldown)
        return delta > cooldown_td

    # @implements FridayStore
    @property
    def avaliable_after(self) -> Optional[datetime]:
        # Return early if the rule doesn't have a last response
        if not self.last_response:
            return None

        # Get the date for when the rule is available next
        return self.last_response + timedelta(seconds=self.cooldown)

    # @implements FridayRule
    def modify(
        self,
        pattern: Optional[re.Pattern],
        chance: float,
        cooldown: int,
        response: str,
        user_id: UserID,
    ):
        self.pattern = pattern
        self.chance = chance
        self.cooldown = cooldown
        self.response = response
        self.modified_by_id = user_id
        self.modified_on = utcnow()

    def _roll(self) -> bool:
        return random.random() < self.chance

    def _match(self, content: str) -> bool:
        if self.pattern:
            return bool(self.pattern.search(content))
        return True

    # @implements FridayRule
    def check(self, content: str) -> bool:
        return self.available and self._roll() and self._match(content)


@dataclass
class FridayGuildData(JsonSerializable, FromDataMixin):
    rules: dict[str, FridayRuleData] = field(default_factory=dict)
    channels: list[ChannelID] = field(default_factory=list)

    # @implements FromDataMixin
    @classmethod
    def try_from_data(cls, data: Any) -> Optional[Self]:
        if isinstance(data, dict):
            return cls(
                rules={
                    name: FridayRuleData.from_data(raw_rule)
                    for name, raw_rule in data.get("rules", {}).items()
                },
                channels=[channel_id for channel_id in data.get("channels", [])],
            )

    # @implements JsonSerializable
    def to_json(self) -> Any:
        return utils.dict_without_falsies(
            rules=utils.dict_without_falsies(
                {name: rule.to_json() for name, rule in self.rules.items()}
            ),
            channels=self.channels,
        )

    def _is_rule_name_available(self, name: str) -> bool:
        return name not in self.rules.keys()

    def is_channel_registered(self, channel_id: ChannelID) -> bool:
        return channel_id in self.channels

    def register_channel(self, channel_id: ChannelID):
        # Check if the channel was already registered
        if self.is_channel_registered(channel_id):
            raise ChannelAlreadyRegistered(channel_id)

        # Register the channel
        self.channels.append(channel_id)

    def unregister_channel(self, channel_id: ChannelID):
        # Check if the channel was not registered
        if not self.is_channel_registered(channel_id):
            raise ChannelNotRegistered(channel_id)

        # Unregister the channel
        self.channels.remove(channel_id)

    def require_rule(self, name: str) -> FridayRuleData:
        if rule := self.rules.get(name):
            return rule
        raise RuleDoesNotExist(name)

    def add_rule(
        self,
        name: str,
        pattern: Optional[str],
        chance: float,
        cooldown: int,
        response: str,
        user_id: UserID,
    ) -> FridayRuleData:
        # Check if the rule already exists
        if not self._is_rule_name_available(name):
            raise RuleAlreadyExists(name)

        # Create and add a new rule
        rule = FridayRuleData(
            name=name,
            pattern=re.compile(pattern, re.IGNORECASE) if pattern else None,
            chance=chance,
            cooldown=cooldown,
            response=response,
            last_response=None,
            hits=0,
            added_by_id=user_id,
            modified_by_id=user_id,
            added_on=utcnow(),
            modified_on=utcnow(),
        )
        self.rules[name] = rule
        return rule

    def modify_rule(
        self,
        name: str,
        pattern: Optional[str],
        chance: float,
        cooldown: int,
        response: str,
        user_id: UserID,
    ) -> FridayRuleData:
        # The rule must exist
        rule = self.require_rule(name)

        # Modify the rule
        rule.modify(
            pattern=re.compile(pattern, re.IGNORECASE) if pattern else None,
            chance=chance,
            cooldown=cooldown,
            response=response,
            user_id=user_id,
        )
        return rule

    def remove_rule(self, name: str) -> FridayRuleData:
        # The rule must exist
        rule = self.require_rule(name)

        # Remove the rule
        del self.rules[name]
        return rule

    def check_rules(self, content: str) -> Optional[FridayRuleData]:
        for rule in self.rules.values():
            if rule.check(content):
                return rule

    def all_rules_matching(
        self, rule_filter: Optional[str], case_sensitive: bool
    ) -> Iterable[FridayRuleData]:
        if not rule_filter:
            yield from self.rules.values()
        else:
            rule_filter = rule_filter if case_sensitive else rule_filter.lower()
            for rule in self.rules.values():
                rule_name: str = rule.name if case_sensitive else rule.name.lower()
                if rule_filter in rule_name:
                    yield rule


def _guilds_defaultdict_factory() -> defaultdict[GuildID, FridayGuildData]:
    return defaultdict(lambda: FridayGuildData())


# @implements FridayStore
@dataclass
class FridayData(JsonSerializable, FromDataMixin):
    """
    Implementation of `FridayStore` using an in-memory object hierarchy.
    """

    guilds: defaultdict[GuildID, FridayGuildData] = field(
        default_factory=_guilds_defaultdict_factory
    )

    # @implements FromDataMixin
    @classmethod
    def try_from_data(cls, data: Any) -> Optional[Self]:
        if isinstance(data, dict):
            # Construct guild data
            guilds = _guilds_defaultdict_factory()
            for raw_guild_id, raw_guild_data in data.get("guilds", {}).items():
                guild_id = int(raw_guild_id)
                guilds[guild_id] = FridayGuildData.from_data(raw_guild_data)

            return cls(guilds=guilds)

    # @implements JsonSerializable
    def to_json(self) -> Any:
        # Omit empty guilds, as well as an empty list of guilds
        return utils.dict_without_falsies(
            guilds=utils.dict_without_falsies(
                {
                    str(guild_id): guild_data.to_json()
                    for guild_id, guild_data in self.guilds.items()
                }
            )
        )

    # @implements FridayStore
    async def is_channel_registered(self, guild: Guild, channel_id: ChannelID) -> bool:
        return self.guilds[guild.id].is_channel_registered(channel_id)

    # @implements FridayStore
    async def register_channel(self, guild: Guild, channel_id: ChannelID):
        return self.guilds[guild.id].register_channel(channel_id)

    # @implements FridayStore
    async def unregister_channel(self, guild: Guild, channel_id: ChannelID):
        return self.guilds[guild.id].unregister_channel(channel_id)

    # @implements FridayStore
    async def require_rule(self, guild: Guild, name: str) -> FridayRule:
        return self.guilds[guild.id].require_rule(name)

    # @implements FridayStore
    async def add_rule(
        self,
        guild: Guild,
        name: str,
        pattern: Optional[str],
        chance: float,
        cooldown: int,
        response: str,
        user_id: UserID,
    ) -> FridayRule:
        return self.guilds[guild.id].add_rule(
            name, pattern, chance, cooldown, response, user_id
        )

    # @implements FridayStore
    async def modify_rule(
        self,
        guild: Guild,
        name: str,
        pattern: Optional[str],
        chance: float,
        cooldown: int,
        response: str,
        user_id: UserID,
    ) -> FridayRule:
        return self.guilds[guild.id].modify_rule(
            name, pattern, chance, cooldown, response, user_id
        )

    # @implements FridayStore
    async def remove_rule(self, guild: Guild, name: str) -> FridayRule:
        return self.guilds[guild.id].remove_rule(name)

    # @implements FridayStore
    async def check_rules(self, guild: Guild, content: str) -> Optional[FridayRule]:
        return self.guilds[guild.id].check_rules(content)

    # @implements FridayStore
    async def update_on_rule_matched(self, rule: FridayRule):
        rule.last_response = utcnow()
        rule.hits += 1

    # @implements FridayStore
    async def get_rules(
        self,
        guild: Guild,
        *,
        rule_filter: Optional[str] = None,
        case_sensitive: bool = False,
        sort: bool = False,
        cap: Optional[int] = None,
    ) -> AsyncIterable[FridayRule]:
        rules = self.guilds[guild.id].all_rules_matching(rule_filter, case_sensitive)
        maybe_sorted_rules = sorted(rules, key=lambda r: r.name) if sort else rules
        for rule in islice(maybe_sorted_rules, cap):
            yield rule
