import re
from datetime import datetime
from typing import List, Optional, Protocol, Set, Tuple

from discord import Guild

from commanderbot.lib import ResponsiveException


class FaqException(ResponsiveException):
    pass


class FaqKeyAlreadyExists(FaqException):
    def __init__(self, key: str):
        self.key: str = key
        super().__init__(f"FAQ `{key}` already exists")


class FaqAliasUnavailable(FaqException):
    def __init__(self, alias: str):
        self.alias: str = alias
        super().__init__(f"FAQ alias `{alias}` is unavailable")


class NoSuchFaq(FaqException):
    def __init__(self, name: str):
        self.name: str = name
        super().__init__(f"No such FAQ `{name}`")


class FaqEntry(Protocol):
    key: str
    added_on: datetime
    modified_on: datetime
    hits: int
    content: str
    link: Optional[str]
    aliases: Set[str]
    tags: Set[str]

    @property
    def sorted_aliases(self) -> List[str]:
        ...

    @property
    def sorted_tags(self) -> List[str]:
        ...


class FaqStore(Protocol):
    """
    Abstracts the data storage and persistence of the FAQ cog.
    """

    async def get_prefix(self, guild: Guild) -> Optional[str]:
        """Get the configured shortcut prefix, if any."""

    async def set_prefix(self, guild: Guild, prefix: Optional[str]) -> Optional[str]:
        """Set the shortcut prefix, if any."""

    async def get_match(self, guild: Guild) -> Optional[re.Pattern]:
        """Get the configured match pattern, if any."""

    async def set_match(
        self, guild: Guild, match: Optional[str]
    ) -> Optional[re.Pattern]:
        """Set the match pattern, if any."""

    async def get_faq_by_name(self, guild: Guild, name: str) -> Optional[FaqEntry]:
        """Return the FAQ matching by exact key or alias, if any."""

    async def require_faq_by_name(self, guild: Guild, name: str) -> FaqEntry:
        """Return the FAQ matching by exact key or alias."""

    async def get_faqs_by_query(
        self, guild: Guild, query: str, cap: int
    ) -> List[FaqEntry]:
        """Return all FAQs matching by key, alias, or tag."""

    async def get_faqs_by_match(
        self, guild: Guild, content: str, cap: int
    ) -> List[FaqEntry]:
        """Return all FAQs matched in the message content, if any."""

    async def increment_faq_hits(self, faq: FaqEntry):
        ...

    async def add_faq(
        self, guild: Guild, key: str, link: str, content: str
    ) -> FaqEntry:
        ...

    async def remove_faq(self, guild: Guild, name: str) -> FaqEntry:
        ...

    async def modify_faq_content(
        self, guild: Guild, name: str, content: str
    ) -> FaqEntry:
        ...

    async def modify_faq_link(
        self, guild: Guild, name: str, link: Optional[str]
    ) -> FaqEntry:
        ...

    async def modify_faq_aliases(
        self, guild: Guild, name: str, aliases: Tuple[str, ...]
    ) -> FaqEntry:
        ...

    async def modify_faq_tags(
        self, guild: Guild, name: str, tags: Tuple[str, ...]
    ) -> FaqEntry:
        ...
