from dataclasses import dataclass, field
from typing import Any, Self

from commanderbot.lib.cogs.database import (
    DatabaseOptions,
    InMemoryDatabaseOptions,
    make_database_options,
)


@dataclass
class AutomodOptions:
    database: DatabaseOptions = field(default_factory=InMemoryDatabaseOptions)

    @classmethod
    def from_dict(cls, options: dict[str, Any]) -> Self:
        database_options = make_database_options(options.get("database"))
        return cls(database=database_options)
