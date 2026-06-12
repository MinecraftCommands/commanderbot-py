from typing import Protocol, runtime_checkable

from commanderbot.lib.databases.json_db.v1 import JsonFileDatabaseAdapter


@runtime_checkable
class DatabaseAdapter(Protocol):
    db: JsonFileDatabaseAdapter


@runtime_checkable
class CogWithStore(Protocol):
    store: DatabaseAdapter
