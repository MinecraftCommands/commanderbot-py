from dataclasses import dataclass, field
from typing import Any, Optional, Type, TypeVar

from commanderbot.lib import FromDataMixin
from commanderbot.lib.cogs.database import (
    DatabaseOptions,
    InMemoryDatabaseOptions,
    make_database_options,
)

ST = TypeVar("ST")


@dataclass
class HelpForumOptions(FromDataMixin):
    database: DatabaseOptions = field(default_factory=InMemoryDatabaseOptions)

    # @overrides FromDataMixin
    @classmethod
    def try_from_data(cls: Type[ST], data: Any) -> Optional[ST]:
        if isinstance(data, dict):
            database_options = make_database_options(data.get("database"))
            return cls(database=database_options)
