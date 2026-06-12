from typing import Protocol, runtime_checkable

from commanderbot.lib.databases.json_db import JsonDB
from commanderbot.lib.databases.json_db.v1 import JsonFileDatabaseAdapter


@runtime_checkable
class CogStore(Protocol):
    db: JsonDB | JsonFileDatabaseAdapter


@runtime_checkable
class CogWithStore(Protocol):
    store: CogStore
