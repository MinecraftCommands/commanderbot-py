from typing import Protocol, runtime_checkable

from commanderbot.lib.cogs.database import JsonFileDatabaseAdapter, SQLDatabaseAdapter


@runtime_checkable
class DatabaseAdapter(Protocol):
    db: JsonFileDatabaseAdapter | SQLDatabaseAdapter


@runtime_checkable
class CogWithStore(Protocol):
    store: DatabaseAdapter
