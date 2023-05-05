from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from itertools import chain
from typing import Any, AsyncIterable, Iterable, Optional, Type, TypeVar, Union

from discord import Guild

from commanderbot.ext.invite.invite_exceptions import (
    GuildInviteNotSet,
    InvalidInviteLink,
    InviteAlreadyExists,
    InviteDoesNotExist,
)
from commanderbot.ext.invite.invite_store import InviteEntry
from commanderbot.lib import FromDataMixin, GuildID, JsonSerializable
from commanderbot.lib.utils.utils import dict_without_falsies, is_invite_link

ST = TypeVar("ST")


@dataclass
class InviteEntryData(JsonSerializable, FromDataMixin):
    key: str
    tags: set[str]
    link: str
    description: Optional[str]
    hits: int
    added_on: datetime
    modified_on: datetime

    # @overrides FromDataMixin
    @classmethod
    def try_from_data(cls: Type[ST], data: Any) -> Optional[ST]:
        if isinstance(data, dict):
            return cls(
                key=data["key"],
                tags=set(data["tags"]),
                link=data["link"],
                description=data["description"],
                hits=data["hits"],
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
            "added_on": self.added_on.isoformat(),
            "modified_on": self.modified_on.isoformat(),
        }

    # @implements InviteEntry
    def modify(
        self,
        *,
        tags: list[str],
        link: str,
        description: Optional[str],
    ):
        self.tags = set(tags)
        self.link = link
        self.description = description
        self.modified_on = datetime.now()

    # @implements InviteEntry
    def format(self) -> str:
        if self.description:
            return f"{self.link} - {self.description}"
        return self.link


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
        # Omit empty entries
        return dict_without_falsies(
            invite_entries={
                key: entry.to_json() for key, entry in self.invite_entries.items()
            },
            guild_key=self.guild_key,
        )

    def __post_init__(self):
        self._rebuild_tag_mappings()

    def _rebuild_tag_mappings(self):
        # Build the tag to invite keys mappings
        for entry in self.invite_entries.values():
            for tag in entry.tags:
                self.invite_entries_by_tag[tag].append(entry)

    def _is_invite_key_available(self, key: str) -> bool:
        # Check whether the given invite key is already in use
        return key not in self.invite_entries.keys()

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
        self, key: str, tags: list[str], link: str, description: Optional[str]
    ) -> InviteEntryData:
        # Check if the invite key already exists
        if not self._is_invite_key_available(key):
            raise InviteAlreadyExists(key)

        # Check if the invite link is valid
        if not is_invite_link(link):
            raise InvalidInviteLink(link)

        # Create and add a new invite entry
        entry = InviteEntryData(
            key, set(tags), link, description, 0, datetime.now(), datetime.now()
        )
        self.invite_entries[key] = entry
        self._rebuild_tag_mappings()

        # Return the newly created invite entry
        return entry

    def modify_invite(
        self, key: str, tags: list[str], link: str, description: Optional[str]
    ) -> InviteEntryData:
        # The invite must exist
        entry = self.require_invite(key)

        # Check if the invite link is valid
        if not is_invite_link(link):
            raise InvalidInviteLink(link)

        # Modify the invite entry
        entry.modify(tags=tags, link=link, description=description)
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
    ) -> InviteEntry:
        return self.guilds[guild.id].add_invite(key, tags, link, description)

    # @implements InviteStore
    async def modify_invite(
        self,
        guild: Guild,
        key: str,
        tags: list[str],
        link: str,
        description: Optional[str],
    ) -> InviteEntry:
        return self.guilds[guild.id].modify_invite(key, tags, link, description)

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
        self, guild: Guild, *, invite_filter: Optional[str] = None
    ) -> AsyncIterable[InviteEntry]:
        for entry in self.guilds[guild.id].invite_entries.values():
            if invite_filter and invite_filter not in entry.key:
                continue
            yield entry

    # @implements InviteStore
    async def get_tags(
        self, guild: Guild, *, tag_filter: Optional[str] = None
    ) -> AsyncIterable[str]:
        for tag in self.guilds[guild.id].invite_entries_by_tag.keys():
            if tag_filter and tag_filter not in tag:
                continue
            yield tag

    # @implements InviteStore
    async def get_invites_and_tags(
        self, guild: Guild, *, item_filter: Optional[str] = None
    ) -> AsyncIterable[Union[InviteEntry, str]]:
        item_gen = chain(
            self.guilds[guild.id].invite_entries.values(),
            self.guilds[guild.id].invite_entries_by_tag.keys(),
        )
        for item in item_gen:
            if item_filter and item_filter not in (
                item if isinstance(item, str) else item.key
            ):
                continue
            yield item

    # @implements InviteStore
    async def set_guild_invite(self, guild: Guild, key: str) -> InviteEntry:
        return self.guilds[guild.id].set_guild_invite(key)

    # @implements InviteStore
    async def clear_guild_invite(self, guild: Guild) -> InviteEntry:
        return self.guilds[guild.id].clear_guild_invite()
