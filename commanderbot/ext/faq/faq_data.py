import re
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from itertools import chain, islice
from typing import Any, AsyncIterable, Iterable, Optional, Self

from discord import Guild
from discord.utils import utcnow

from commanderbot.ext.faq.faq_exceptions import (
    FaqAliasAlreadyExists,
    FaqAliasMatchesExistingKey,
    FaqDoesNotExist,
    FaqKeyAlreadyExists,
    FaqKeyMatchesExistingAlias,
    FaqKeyMatchesOwnAlias,
    InvalidMatchPattern,
    InvalidPrefixPattern,
    MatchPatternNotSet,
    PrefixPatternNotSet,
)
from commanderbot.ext.faq.faq_store import FaqEntry
from commanderbot.lib import FromDataMixin, GuildID, JsonSerializable, UserID
from commanderbot.lib.utils import dict_without_falsies

TERM_SPLIT_PATTERN = re.compile(r"\W+")


@dataclass
class FaqEntryData(JsonSerializable, FromDataMixin):
    key: str
    aliases: set[str]
    tags: set[str]
    content: str
    hits: int
    added_by_id: UserID
    modified_by_id: UserID
    added_on: datetime
    modified_on: datetime

    match_terms: set[str] = field(init=False, default_factory=set)

    # @overrides FromDataMixin
    @classmethod
    def try_from_data(cls, data: Any) -> Optional[Self]:
        if isinstance(data, dict):
            return cls(
                key=data["key"],
                aliases=set(data.get("aliases", [])),
                tags=set(data.get("tags", [])),
                content=data["content"],
                hits=data["hits"],
                added_by_id=data["added_by_id"],
                modified_by_id=data["modified_by_id"],
                added_on=datetime.fromisoformat(data["added_on"]),
                modified_on=datetime.fromisoformat(data["modified_on"]),
            )

    # @implements JsonSerializable
    def to_json(self) -> Any:
        return {
            "key": self.key,
            "aliases": list(self.aliases),
            "tags": list(self.tags),
            "content": self.content,
            "hits": self.hits,
            "added_by_id": self.added_by_id,
            "modified_by_id": self.modified_by_id,
            "added_on": self.added_on.isoformat(),
            "modified_on": self.modified_on.isoformat(),
        }

    def __post_init__(self):
        self._rebuild_match_terms()

    def _rebuild_match_terms(self):
        # Build match terms from keys, aliases, and tags
        self.match_terms.clear()
        for term in (self.key, *self.aliases, *self.tags):
            self.match_terms.add(term)
            for word in TERM_SPLIT_PATTERN.split(term):
                self.match_terms.add(word)

    # @implements FaqEntry
    @property
    def sorted_aliases(self) -> list[str]:
        return sorted(self.aliases)

    # @implements FaqEntry
    @property
    def sorted_tags(self) -> list[str]:
        return sorted(self.tags)

    # @implements FaqEntry
    def modify(
        self,
        aliases: list[str],
        tags: list[str],
        content: str,
        user_id: UserID,
    ):
        self.aliases = set(aliases)
        self.tags = set(tags)
        self.content = content
        self.modified_by_id = user_id
        self.modified_on = utcnow()

        self._rebuild_match_terms()

    # @implements FaqEntry
    def matches_query(self, query: str) -> bool:
        for term in TERM_SPLIT_PATTERN.split(query):
            if term in self.match_terms:
                return True
        return False


@dataclass
class FaqGuildData(JsonSerializable, FromDataMixin):
    faq_entries: dict[str, FaqEntryData] = field(default_factory=dict)
    faq_entries_by_alias: dict[str, FaqEntryData] = field(
        init=False, default_factory=dict
    )
    prefix: Optional[re.Pattern] = None
    match: Optional[re.Pattern] = None

    # @overrides FromDataMixin
    @classmethod
    def try_from_data(cls, data: Any) -> Optional[Self]:
        # Note that aliases will be constructed from entries, during post-init
        if isinstance(data, dict):
            raw_prefix = data.get("prefix")
            raw_match = data.get("match")
            return cls(
                faq_entries={
                    key: FaqEntryData.from_data(raw_entry)
                    for key, raw_entry in data.get("faq_entries", {}).items()
                },
                prefix=re.compile(raw_prefix) if raw_prefix else None,
                match=re.compile(raw_match) if raw_match else None,
            )

    # @implements JsonSerializable
    def to_json(self) -> Any:
        return dict_without_falsies(
            # Omit empty entries
            faq_entries=dict_without_falsies(
                {key: entry.to_json() for key, entry in self.faq_entries.items()}
            ),
            prefix=self.prefix.pattern if self.prefix else None,
            match=self.match.pattern if self.match else None,
        )

    def __post_init__(self):
        self._rebuild_alias_mappings()

    def _rebuild_alias_mappings(self):
        # Build the list of aliases from entries
        self.faq_entries_by_alias.clear()
        for entry in self.faq_entries.values():
            for alias in entry.aliases:
                self.faq_entries_by_alias[alias] = entry

    def _is_faq_key_available(self, key: str) -> bool:
        return key not in self.faq_entries.keys()

    def _is_faq_alias_available(self, alias: str) -> bool:
        return alias not in self.faq_entries_by_alias.keys()

    def require_faq(self, key: str) -> FaqEntryData:
        if entry := self.faq_entries.get(key):
            return entry
        raise FaqDoesNotExist(key)

    def require_prefix_pattern(self) -> re.Pattern:
        if pattern := self.prefix:
            return pattern
        raise PrefixPatternNotSet

    def require_match_pattern(self) -> re.Pattern:
        if pattern := self.match:
            return pattern
        raise MatchPatternNotSet

    def get_prefix_pattern(self) -> Optional[re.Pattern]:
        return self.prefix

    def get_match_pattern(self) -> Optional[re.Pattern]:
        return self.match

    def add_faq(
        self,
        key: str,
        aliases: list[str],
        tags: list[str],
        content: str,
        user_id: UserID,
    ) -> FaqEntryData:
        # Check if the faq key already exists
        if not self._is_faq_key_available(key):
            raise FaqKeyAlreadyExists(key)

        # Check if the faq key matches an existing faq alias
        if not self._is_faq_alias_available(key):
            raise FaqKeyMatchesExistingAlias(key)

        # Check if the faq key is in this faq's aliases
        if key in aliases:
            raise FaqKeyMatchesOwnAlias

        # Check the faq aliases
        for alias in aliases:
            # Check if the faq alias already exists
            if not self._is_faq_alias_available(alias):
                raise FaqAliasAlreadyExists(alias)

            # Check if the faq alias matches an existing faq key
            if not self._is_faq_key_available(alias):
                raise FaqAliasMatchesExistingKey(alias)

        # Create and add a new faq entry
        entry = FaqEntryData(
            key,
            set(aliases),
            set(tags),
            content,
            0,
            user_id,
            user_id,
            utcnow(),
            utcnow(),
        )
        self.faq_entries[key] = entry
        self._rebuild_alias_mappings()
        return entry

    def modify_faq(
        self,
        key: str,
        aliases: list[str],
        tags: list[str],
        content: str,
        user_id: UserID,
    ) -> FaqEntryData:
        # The faq must exist
        entry = self.require_faq(key)

        # Check if the faq key is in this faq's aliases
        if entry.key in aliases:
            raise FaqKeyMatchesOwnAlias

        # Check the new faq aliases
        new_aliases = set(aliases).difference(entry.aliases)
        for alias in new_aliases:
            # Check if the faq alias already exists
            if not self._is_faq_alias_available(alias):
                raise FaqAliasAlreadyExists(alias)

            # Check if the faq alias matches an existing faq key
            if not self._is_faq_key_available(alias):
                raise FaqAliasMatchesExistingKey(alias)

        # Modify the faq entry
        entry.modify(aliases, tags, content, user_id)
        self._rebuild_alias_mappings()
        return entry

    def remove_faq(self, key: str) -> FaqEntryData:
        # The faq must exist
        entry = self.require_faq(key)

        # Remove entry
        del self.faq_entries[key]
        self._rebuild_alias_mappings()
        return entry

    def query_faq(self, query: str) -> Optional[FaqEntryData]:
        # Return the faq entry by key, if it exists
        if entry := self.faq_entries.get(query):
            return entry
        # Otherwise try to return it by alias
        return self.faq_entries_by_alias.get(query)

    def query_faqs_by_match(self, content: str) -> Iterable[FaqEntryData]:
        # If a match pattern is configured, look for matches in `content`
        if self.match:
            # Find all instances of the match pattern in `content`
            # and try to find faqs that match it
            queried_faq_entries: set[str] = set()
            for match in self.match.finditer(content):
                query: str = "".join(match.groups())
                entry: Optional[FaqEntryData] = self.query_faq(query)

                # Make sure to not return duplicate faqs
                if entry and (entry.key not in queried_faq_entries):
                    queried_faq_entries.add(entry.key)
                    yield entry

    def query_faqs_by_terms(self, query: str) -> Iterable[FaqEntryData]:
        # Yield faqs that match the query
        for entry in self.faq_entries.values():
            if entry.matches_query(query):
                yield entry

    def all_faqs_matching(
        self, faq_filter: Optional[str], case_sensitive: bool
    ) -> Iterable[FaqEntryData]:
        if not faq_filter:
            yield from self.faq_entries.values()
        else:
            faq_filter = faq_filter if case_sensitive else faq_filter.lower()
            for entry in self.faq_entries.values():
                faq_key: str = entry.key if case_sensitive else entry.key.lower()
                if faq_filter in faq_key:
                    yield entry

    def all_faq_aliases_matching(
        self, alias_filter: Optional[str], case_sensitive: bool
    ) -> Iterable[tuple[str, FaqEntryData]]:
        if not alias_filter:
            for alias, entry in self.faq_entries_by_alias.items():
                yield (alias, entry)
        else:
            alias_filter = alias_filter if case_sensitive else alias_filter.lower()
            for alias, entry in self.faq_entries_by_alias.items():
                faq_alias: str = alias if case_sensitive else alias.lower()
                if alias_filter in faq_alias:
                    yield (alias, entry)

    def set_prefix_pattern(self, prefix: str) -> re.Pattern:
        try:
            self.prefix = re.compile(prefix)
            return self.prefix
        except re.error as ex:
            raise InvalidPrefixPattern(prefix, str(ex))

    def clear_prefix_pattern(self) -> re.Pattern:
        pattern = self.require_prefix_pattern()
        self.prefix = None
        return pattern

    def set_match_pattern(self, match: str) -> re.Pattern:
        try:
            self.match = re.compile(match)
            return self.match
        except re.error as ex:
            raise InvalidMatchPattern(match, str(ex))

    def clear_match_pattern(self) -> re.Pattern:
        pattern = self.require_match_pattern()
        self.match = None
        return pattern


def _guilds_defaultdict_factory() -> defaultdict[GuildID, FaqGuildData]:
    return defaultdict(lambda: FaqGuildData())


# @implements FaqStore
@dataclass
class FaqData(JsonSerializable, FromDataMixin):
    """
    Implementation of `FaqStore` using an in-memory object hierarchy.
    """

    guilds: defaultdict[GuildID, FaqGuildData] = field(
        default_factory=_guilds_defaultdict_factory
    )

    # @overrides FromDataMixin
    @classmethod
    def try_from_data(cls, data: Any) -> Optional[Self]:
        if isinstance(data, dict):
            # Construct guild data
            guilds = _guilds_defaultdict_factory()
            for raw_guild_id, raw_guild_data in data.get("guilds", {}).items():
                guild_id = int(raw_guild_id)
                guilds[guild_id] = FaqGuildData.from_data(raw_guild_data)

            return cls(guilds=guilds)

    # @implements JsonSerializable
    def to_json(self) -> Any:
        # Omit empty guilds, as well as an empty list of guilds
        return dict_without_falsies(
            guilds=dict_without_falsies(
                {
                    str(guild_id): guild_data.to_json()
                    for guild_id, guild_data in self.guilds.items()
                }
            )
        )

    # @implements FaqStore
    async def require_faq(self, guild: Guild, key: str) -> FaqEntry:
        return self.guilds[guild.id].require_faq(key)

    # @implements FaqStore
    async def require_prefix_pattern(self, guild: Guild) -> re.Pattern:
        return self.guilds[guild.id].require_prefix_pattern()

    # @implements FaqStore
    async def require_match_pattern(self, guild: Guild) -> re.Pattern:
        return self.guilds[guild.id].require_match_pattern()

    # @implements FaqStore
    async def get_prefix_pattern(self, guild: Guild) -> Optional[re.Pattern]:
        return self.guilds[guild.id].get_prefix_pattern()

    # @implements FaqStore
    async def get_match_pattern(self, guild: Guild) -> Optional[re.Pattern]:
        return self.guilds[guild.id].get_match_pattern()

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
        return self.guilds[guild.id].add_faq(key, aliases, tags, content, user_id)

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
        return self.guilds[guild.id].modify_faq(key, aliases, tags, content, user_id)

    # @implements FaqStore
    async def increment_faq_hits(self, entry: FaqEntry):
        entry.hits += 1

    # @implements FaqStore
    async def remove_faq(self, guild: Guild, key: str) -> FaqEntry:
        return self.guilds[guild.id].remove_faq(key)

    # @implements FaqStore
    async def query_faq(self, guild: Guild, query: str) -> Optional[FaqEntry]:
        return self.guilds[guild.id].query_faq(query)

    # @implements FaqStore
    async def query_faqs_by_match(
        self,
        guild: Guild,
        content: str,
        *,
        sort: bool = False,
        cap: Optional[int] = None,
    ) -> AsyncIterable[FaqEntry]:
        entries = self.guilds[guild.id].query_faqs_by_match(content)
        maybe_sorted = sorted(entries, key=lambda entry: entry.key) if sort else entries
        for entry in islice(maybe_sorted, cap):
            yield entry

    # @implements FaqStore
    async def query_faqs_by_terms(
        self, guild: Guild, query: str, *, sort: bool = False, cap: Optional[int] = None
    ) -> AsyncIterable[FaqEntry]:
        entries = self.guilds[guild.id].query_faqs_by_terms(query)
        maybe_sorted = sorted(entries, key=lambda entry: entry.key) if sort else entries
        for entry in islice(maybe_sorted, cap):
            yield entry

    # @implements FaqStore
    async def get_faqs(
        self,
        guild: Guild,
        *,
        faq_filter: Optional[str] = None,
        case_sensitive: bool = False,
        sort: bool = False,
        cap: Optional[int] = None,
    ) -> AsyncIterable[FaqEntry]:
        entries = self.guilds[guild.id].all_faqs_matching(faq_filter, case_sensitive)
        maybe_sorted_entries = (
            sorted(entries, key=lambda entry: entry.key) if sort else entries
        )
        for entry in islice(maybe_sorted_entries, cap):
            yield entry

    # @implements FaqStore
    async def get_faqs_and_aliases(
        self,
        guild: Guild,
        *,
        item_filter: Optional[str] = None,
        case_sensitive: bool = False,
        sort: bool = False,
        cap: Optional[int] = None,
    ) -> AsyncIterable[FaqEntry | tuple[str, FaqEntry]]:
        items = chain(
            self.guilds[guild.id].all_faqs_matching(item_filter, case_sensitive),
            self.guilds[guild.id].all_faq_aliases_matching(item_filter, case_sensitive),
        )

        def item_cmp(item: FaqEntry | tuple[str, FaqEntry]):
            if isinstance(item, tuple):
                return item[0]
            return item.key

        maybe_sorted_items = sorted(items, key=item_cmp) if sort else items
        for item in islice(maybe_sorted_items, cap):
            yield item

    # @implements FaqStore
    async def set_prefix_pattern(self, guild: Guild, prefix: str) -> re.Pattern:
        return self.guilds[guild.id].set_prefix_pattern(prefix)

    # @implements FaqStore
    async def clear_prefix_pattern(self, guild: Guild) -> re.Pattern:
        return self.guilds[guild.id].clear_prefix_pattern()

    # @implements FaqStore
    async def set_match_pattern(self, guild: Guild, match: str) -> re.Pattern:
        return self.guilds[guild.id].set_match_pattern(match)

    # @implements FaqStore
    async def clear_match_pattern(self, guild: Guild) -> re.Pattern:
        return self.guilds[guild.id].clear_match_pattern()
