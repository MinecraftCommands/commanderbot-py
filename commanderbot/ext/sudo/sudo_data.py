from enum import Enum, auto
from typing import Protocol, runtime_checkable

from commanderbot.lib.cogs.database import JsonFileDatabaseAdapter, SQLDatabaseAdapter


@runtime_checkable
class DatabaseAdapter(Protocol):
    db: JsonFileDatabaseAdapter | SQLDatabaseAdapter


@runtime_checkable
class CogUsesStore(Protocol):
    store: DatabaseAdapter


class SyncType(Enum):
    SYNC_ONLY = auto()
    COPY = auto()
    REMOVE = auto()
