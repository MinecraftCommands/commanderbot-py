from dataclasses import dataclass, field
from typing import Any, Optional, Self

from commanderbot.lib import FromDataMixin
from commanderbot.lib.cogs.database import (
    DatabaseOptions,
    InMemoryDatabaseOptions,
    make_database_options,
)


@dataclass
class FaqOptions(FromDataMixin):
    database: DatabaseOptions = field(default_factory=InMemoryDatabaseOptions)

    allow_prefix: bool = True
    allow_match: bool = True
    term_cap: int = 10
    match_cap: int = 3

    # @implements FromDataMixin
    @classmethod
    def try_from_data(cls, data: Any) -> Optional[Self]:
        if isinstance(data, dict):
            database_options = make_database_options(data.get("database"))
            return cls(
                database=database_options,
                allow_prefix=data.get("allow_prefix", True),
                allow_match=data.get("allow_match", True),
                term_cap=data.get("term_cap", 10),
                match_cap=data.get("match_cap", 3),
            )
