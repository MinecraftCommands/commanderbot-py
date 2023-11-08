import re
from datetime import datetime
from typing import AsyncIterable, Optional, Protocol

from discord import Guild

from commanderbot.lib import UserID


class FaqEntry(Protocol):
    key: str
    aliases: set[str]
    tags: set[str]
    content: str
    hits: int
    added_by_id: UserID
    modified_by_id: UserID
    added_on: datetime
    modified_on: datetime

    @property
    def sorted_aliases(self) -> list[str]:
        ...

    @property
    def sorted_tags(self) -> list[str]:
        ...

    def modify(
        self,
        aliases: list[str],
        tags: list[str],
        content: str,
        user_id: UserID,
    ):
        ...

    def matches_query(self, query: str) -> bool:
        ...


class FaqStore(Protocol):
    """
    Abstracts the data storage and persistence of the faq cog
    """

    async def require_faq(self, guild: Guild, key: str) -> FaqEntry:
        ...

    async def require_prefix_pattern(self, guild: Guild) -> re.Pattern:
        ...

    async def require_match_pattern(self, guild: Guild) -> re.Pattern:
        ...

    async def get_prefix_pattern(self, guild: Guild) -> Optional[re.Pattern]:
        ...

    async def get_match_pattern(self, guild: Guild) -> Optional[re.Pattern]:
        ...

    async def add_faq(
        self,
        guild: Guild,
        key: str,
        aliases: list[str],
        tags: list[str],
        content: str,
        user_id: UserID,
    ) -> FaqEntry:
        ...

    async def modify_faq(
        self,
        guild: Guild,
        key: str,
        aliases: list[str],
        tags: list[str],
        content: str,
        user_id: UserID,
    ) -> FaqEntry:
        ...

    async def increment_faq_hits(self, entry: FaqEntry):
        ...

    async def remove_faq(self, guild: Guild, key: str) -> FaqEntry:
        ...

    async def query_faq(self, guild: Guild, query: str) -> Optional[FaqEntry]:
        ...

    def query_faqs_by_match(
        self,
        guild: Guild,
        content: str,
        *,
        sort: bool = False,
        cap: Optional[int] = None
    ) -> AsyncIterable[FaqEntry]:
        ...

    def query_faqs_by_terms(
        self, guild: Guild, query: str, *, sort: bool = False, cap: Optional[int] = None
    ) -> AsyncIterable[FaqEntry]:
        ...

    def get_faqs(
        self,
        guild: Guild,
        *,
        faq_filter: Optional[str] = None,
        case_sensitive: bool = False,
        sort: bool = False,
        cap: Optional[int] = None
    ) -> AsyncIterable[FaqEntry]:
        ...

    def get_faqs_and_aliases(
        self,
        guild: Guild,
        *,
        item_filter: Optional[str] = None,
        case_sensitive: bool = False,
        sort: bool = False,
        cap: Optional[int] = None
    ) -> AsyncIterable[FaqEntry | tuple[str, FaqEntry]]:
        ...

    async def set_prefix_pattern(self, guild: Guild, prefix: str) -> re.Pattern:
        ...

    async def clear_prefix_pattern(self, guild: Guild) -> re.Pattern:
        ...

    async def set_match_pattern(self, guild: Guild, match: str) -> re.Pattern:
        ...

    async def clear_match_pattern(self, guild: Guild) -> re.Pattern:
        ...
