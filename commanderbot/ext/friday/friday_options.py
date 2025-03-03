from dataclasses import dataclass, field
from typing import Any, Optional, Self

from commanderbot.lib import FromDataMixin
from commanderbot.lib.cogs.database import (
    DatabaseOptions,
    InMemoryDatabaseOptions,
    make_database_options,
)


@dataclass
class FridayOptions(FromDataMixin):
    database: DatabaseOptions = field(default_factory=InMemoryDatabaseOptions)

    # @implements FromDataMixin
    @classmethod
    def try_from_data(cls, data: Any) -> Optional[Self]:
        database_options = make_database_options(data.get("database"))
        return cls(database=database_options)
