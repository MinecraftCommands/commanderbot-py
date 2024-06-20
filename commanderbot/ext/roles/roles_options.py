from dataclasses import dataclass, field
from typing import Any

from commanderbot.lib.cogs.database import (
    DatabaseOptions,
    InMemoryDatabaseOptions,
    make_database_options,
)


@dataclass
class RolesOptions:
    database: DatabaseOptions = field(default_factory=InMemoryDatabaseOptions)

    @staticmethod
    def from_dict(options: dict[str, Any]) -> "RolesOptions":
        database_options = make_database_options(options.get("database"))
        return RolesOptions(database=database_options)
