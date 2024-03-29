from datetime import datetime
from typing import AsyncIterable, Optional, Protocol

from discord import Guild

from commanderbot.lib import UserID


class InviteEntry(Protocol):
    key: str
    tags: set[str]
    link: str
    description: Optional[str]
    hits: int
    added_by_id: UserID
    modified_by_id: UserID
    added_on: datetime
    modified_on: datetime

    @property
    def sorted_tags(self) -> list[str]:
        ...

    def modify(
        self,
        tags: list[str],
        link: str,
        description: Optional[str],
        user_id: UserID,
    ):
        ...


class InviteStore(Protocol):
    """
    Abstracts the data storage and persistence of the invite cog
    """

    async def require_invite(self, guild: Guild, key: str) -> InviteEntry:
        ...

    async def require_guild_invite(self, guild: Guild) -> InviteEntry:
        ...

    async def add_invite(
        self,
        guild: Guild,
        key: str,
        tags: list[str],
        link: str,
        description: Optional[str],
        user_id: UserID,
    ) -> InviteEntry:
        ...

    async def modify_invite(
        self,
        guild: Guild,
        key: str,
        tags: list[str],
        link: str,
        description: Optional[str],
        user_id: UserID,
    ) -> InviteEntry:
        ...

    async def increment_invite_hits(self, entry: InviteEntry):
        ...

    async def remove_invite(self, guild: Guild, key: str) -> InviteEntry:
        ...

    def query_invites(self, guild: Guild, query: str) -> AsyncIterable[InviteEntry]:
        ...

    def get_invites(
        self,
        guild: Guild,
        *,
        invite_filter: Optional[str] = None,
        case_sensitive: bool = False,
        sort: bool = False,
        cap: Optional[int] = None
    ) -> AsyncIterable[InviteEntry]:
        ...

    def get_tags(
        self,
        guild: Guild,
        *,
        tag_filter: Optional[str] = None,
        case_sensitive: bool = False,
        sort: bool = False,
        cap: Optional[int] = None
    ) -> AsyncIterable[str]:
        ...

    def get_invites_and_tags(
        self,
        guild: Guild,
        *,
        item_filter: Optional[str] = None,
        case_sensitive: bool = False,
        sort: bool = False,
        cap: Optional[int] = None
    ) -> AsyncIterable[InviteEntry | str]:
        ...

    async def set_guild_invite(self, guild: Guild, key: str) -> InviteEntry:
        ...

    async def clear_guild_invite(self, guild: Guild) -> InviteEntry:
        ...
