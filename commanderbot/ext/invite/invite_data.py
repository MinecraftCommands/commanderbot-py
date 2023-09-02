from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from itertools import chain, islice
from typing import Any, AsyncIterable, Iterable, Optional, Type, TypeVar, Union

from discord import Guild

from commanderbot.ext.invite.invite_exceptions import (
    GuildInviteNotSet,
    InvalidInviteLink,
    InviteDoesNotExist,
    InviteKeyAlreadyExists,
    InviteKeyMatchesExistingTag,
    InviteKeyMatchesOwnTag,
    InviteTagMatchesExistingKey,
)
from commanderbot.ext.invite.invite_store import InviteEntry
from commanderbot.lib import FromDataMixin, GuildID, JsonSerializable, UserID
from commanderbot.lib.utils.utils import dict_without_falsies, is_invite_link

ST = TypeVar("ST")


@dataclass
class InviteEntryData(JsonSerializable, FromDataMixin):
    key: str
    tags: set[str]
    link: str
    description: Optional[str]
    hits: int
    added_by_id: UserID
    modified_by_id: UserID
    added_on: datetime
    modified_on: datetime

    # @overrides FromDataMixin
    @classmethod
    def try_from_data(cls: Type[ST], data: Any) -> Optional[ST]:
        if isinstance(data, dict):
            return cls(
                key=data["key"],
                tags=set(data.get("tags", [])),
                link=data["link"],
                description=data["description"],
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
            "tags": list(self.tags),
            "link": self.link,
            "description": self.description,
            "hits": self.hits,
            "added_by_id": self.added_by_id,
            "modified_by_id": self.modified_by_id,
            "added_on": self.added_on.isoformat(),
            "modified_on": self.modified_on.isoformat(),
        }

    # @implements InviteEntry
    @property
    def sorted_tags(self) -> list[str]:
        return sorted(self.tags)

    # @implements InviteEntry
    def modify(
        self,
        tags: list[str],
        link: str,
        description: Optional[str],
        user_id: UserID,
    ):
        self.tags = set(tags)
        self.link = link
        self.description = description
        self.modified_by_id = user_id
        self.modified_on = datetime.now()


@dataclass
class InviteGuildData(JsonSerializable, FromDataMixin):
    invite_entries: dict[str, InviteEntryData] = field(default_factory=dict)
    invite_entries_by_tag: defaultdict[str, list[InviteEntryData]] = field(
        init=False, default_factory=lambda: defaultdict(list)
    )
    guild_key: Optional[str] = None

    # @overrides FromDataMixin
    @classmethod
    def try_from_data(cls: Type[ST], data: Any) -> Optional[ST]:
        # Note that tags will be constructed from entries, during post-init
        if isinstance(data, dict):
            return cls(
                invite_entries={
                    key: InviteEntryData.from_data(raw_entry)
                    for key, raw_entry in data.get("invite_entries", {}).items()
                },
                guild_key=data.get("guild_key"),
            )

    # @implements JsonSerializable
    def to_json(self) -> Any:
        return dict_without_falsies(
            # Omit empty entries
            invite_entries=dict_without_falsies(
                {key: entry.to_json() for key, entry in self.invite_entries.items()},
            ),
            guild_key=self.guild_key,
        )

    def __post_init__(self):
        self._rebuild_tag_mappings()

    def _rebuild_tag_mappings(self):
        # Build the tag to invite keys mappings
        self.invite_entries_by_tag.clear()
        for entry in self.invite_entries.values():
            for tag in entry.tags:
                self.invite_entries_by_tag[tag].append(entry)

    def _is_invite_key_available(self, key: str) -> bool:
        # Check whether the given invite key is already in use
        return key not in self.invite_entries.keys()

    def _is_invite_tag_available(self, tag: str) -> bool:
        # Check whether the given invite tag is already in use
        return tag not in self.invite_entries_by_tag.keys()

    def require_invite(self, key: str) -> InviteEntryData:
        # Returns the invite entry if it exists
        if entry := self.invite_entries.get(key):
            return entry
        # Otherwise, raise
        raise InviteDoesNotExist(key)

    def require_guild_invite(self) -> InviteEntryData:
        # Returns the guild invite if it exists
        if self.guild_key and (entry := self.invite_entries.get(self.guild_key)):
            return entry
        # Otherwise, raise
        raise GuildInviteNotSet

    def add_invite(
        self,
        key: str,
        tags: list[str],
        link: str,
        description: Optional[str],
        user_id: UserID,
    ) -> InviteEntryData:
        # Check if the invite key already exists
        if not self._is_invite_key_available(key):
            raise InviteKeyAlreadyExists(key)

        # Check if the invite key matches an existing invite tag
        if not self._is_invite_tag_available(key):
            raise InviteKeyMatchesExistingTag(key)

        # Check if the invite key is in this invite's tags
        if key in tags:
            raise InviteKeyMatchesOwnTag

        # Check the invite tags
        for tag in tags:
            # Check if the invite tag matches an existing invite key
            if not self._is_invite_key_available(tag):
                raise InviteTagMatchesExistingKey(tag)

        # Check if the invite link is valid
        if not is_invite_link(link):
            raise InvalidInviteLink(link)

        # Create and add a new invite entry
        entry = InviteEntryData(
            key,
            set(tags),
            link,
            description,
            0,
            user_id,
            user_id,
            datetime.now(),
            datetime.now(),
        )
        self.invite_entries[key] = entry
        self._rebuild_tag_mappings()
        return entry

    def modify_invite(
        self,
        key: str,
        tags: list[str],
        link: str,
        description: Optional[str],
        user_id: UserID,
    ) -> InviteEntryData:
        # The invite must exist
        entry = self.require_invite(key)

        # Check if the invite key is in this invite's tags
        if entry.key in tags:
            raise InviteKeyMatchesOwnTag

        # Check the invite tags
        for tag in tags:
            # Check if the invite tag matches an existing invite key
            if not self._is_invite_key_available(tag):
                raise InviteTagMatchesExistingKey(tag)

        # Check if the invite link is valid
        if not is_invite_link(link):
            raise InvalidInviteLink(link)

        # Modify the invite entry
        entry.modify(tags, link, description, user_id)
        self._rebuild_tag_mappings()
        return entry

    def remove_invite(self, key: str) -> InviteEntryData:
        # The invite must exist
        entry = self.require_invite(key)

        # Remove entry
        del self.invite_entries[key]
        self._rebuild_tag_mappings()

        # Clear guild key if it was set to this entry
        if self.guild_key == entry.key:
            self.guild_key = None

        return entry

    def query_invites(self, query: str) -> Iterable[InviteEntryData]:
        # First, check for an exact match by key
        if entry := self.invite_entries.get(query):
            yield entry
        # Next, check if it matches any tags
        elif entries := self.invite_entries_by_tag.get(query):
            yield from entries

    def all_invites_matching(
        self, invite_filter: Optional[str], case_sensitive: bool
    ) -> Iterable[InviteEntryData]:
        if not invite_filter:
            yield from self.invite_entries.values()
        else:
            invite_filter = invite_filter if case_sensitive else invite_filter.lower()
            for entry in self.invite_entries.values():
                invite_key: str = entry.key if case_sensitive else entry.key.lower()
                if invite_filter in invite_key:
                    yield entry

    def all_tags_matching(
        self, tag_filter: Optional[str], case_sensitive: bool
    ) -> Iterable[str]:
        if not tag_filter:
            yield from self.invite_entries_by_tag.keys()
        else:
            tag_filter = tag_filter if case_sensitive else tag_filter.lower()
            for tag in self.invite_entries_by_tag.keys():
                invite_tag: str = tag if case_sensitive else tag.lower()
                if tag_filter in invite_tag:
                    yield tag

    def set_guild_invite(self, key: str) -> InviteEntryData:
        entry = self.require_invite(key)
        self.guild_key = entry.key
        return entry

    def clear_guild_invite(self) -> InviteEntryData:
        entry = self.require_guild_invite()
        self.guild_key = None
        return entry


def _guilds_defaultdict_factory() -> defaultdict[GuildID, InviteGuildData]:
    return defaultdict(lambda: InviteGuildData())


# @implements InviteStore
@dataclass
class InviteData(JsonSerializable, FromDataMixin):
    """
    Implementation of `InviteStore` using an in-memory object hierarchy.
    """

    guilds: defaultdict[GuildID, InviteGuildData] = field(
        default_factory=_guilds_defaultdict_factory
    )

    # @overrides FromDataMixin
    @classmethod
    def try_from_data(cls: Type[ST], data: Any) -> Optional[ST]:
        if isinstance(data, dict):
            # Construct guild data
            guilds = _guilds_defaultdict_factory()
            for raw_guild_id, raw_guild_data in data.get("guilds", {}).items():
                guild_id = int(raw_guild_id)
                guilds[guild_id] = InviteGuildData.from_data(raw_guild_data)

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

    # @implements InviteStore
    async def require_invite(self, guild: Guild, key: str) -> InviteEntry:
        return self.guilds[guild.id].require_invite(key)

    # @implements InviteStore
    async def require_guild_invite(self, guild: Guild) -> InviteEntry:
        return self.guilds[guild.id].require_guild_invite()

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
        return self.guilds[guild.id].add_invite(key, tags, link, description, user_id)

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
        return self.guilds[guild.id].modify_invite(
            key, tags, link, description, user_id
        )

    # @implements InviteStore
    async def increment_invite_hits(self, entry: InviteEntry):
        entry.hits += 1

    # @implements InviteStore
    async def remove_invite(self, guild: Guild, key: str) -> InviteEntry:
        return self.guilds[guild.id].remove_invite(key)

    # @implements InviteStore
    async def query_invites(
        self, guild: Guild, query: str
    ) -> AsyncIterable[InviteEntry]:
        for entry in self.guilds[guild.id].query_invites(query):
            yield entry

    # @implements InviteStore
    async def get_invites(
        self,
        guild: Guild,
        *,
        invite_filter: Optional[str] = None,
        case_sensitive: bool = False,
        sort: bool = False,
        cap: Optional[int] = None,
    ) -> AsyncIterable[InviteEntry]:
        entries = self.guilds[guild.id].all_invites_matching(
            invite_filter, case_sensitive
        )
        maybe_sorted_entries = (
            sorted(entries, key=lambda entry: entry.key) if sort else entries
        )
        for entry in islice(maybe_sorted_entries, cap):
            yield entry

    # @implements InviteStore
    async def get_tags(
        self,
        guild: Guild,
        *,
        tag_filter: Optional[str] = None,
        case_sensitive: bool = False,
        sort: bool = False,
        cap: Optional[int] = None,
    ) -> AsyncIterable[str]:
        tags = self.guilds[guild.id].all_tags_matching(tag_filter, case_sensitive)
        maybe_sorted_tags = sorted(tags) if sort else tags
        for tag in islice(maybe_sorted_tags, cap):
            yield tag

    # @implements InviteStore
    async def get_invites_and_tags(
        self,
        guild: Guild,
        *,
        item_filter: Optional[str] = None,
        case_sensitive: bool = False,
        sort: bool = False,
        cap: Optional[int] = None,
    ) -> AsyncIterable[Union[InviteEntry, str]]:
        items = chain(
            self.guilds[guild.id].all_invites_matching(item_filter, case_sensitive),
            self.guilds[guild.id].all_tags_matching(item_filter, case_sensitive),
        )

        def item_cmp(item: Union[InviteEntry, str]) -> str:
            return item if isinstance(item, str) else item.key

        maybe_sorted_items = sorted(items, key=item_cmp) if sort else items
        for item in islice(maybe_sorted_items, cap):
            yield item

    # @implements InviteStore
    async def set_guild_invite(self, guild: Guild, key: str) -> InviteEntry:
        return self.guilds[guild.id].set_guild_invite(key)

    # @implements InviteStore
    async def clear_guild_invite(self, guild: Guild) -> InviteEntry:
        return self.guilds[guild.id].clear_guild_invite()
