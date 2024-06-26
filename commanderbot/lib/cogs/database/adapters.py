import asyncio
from dataclasses import dataclass, field
from logging import Logger, getLogger
from pathlib import Path
from typing import Callable, Generic, Optional, Protocol, TypeVar

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.ext.asyncio.engine import AsyncConnection

from commanderbot.lib.cogs.database.options import JsonFileDatabaseOptions, SQLiteDatabaseOptions
from commanderbot.lib.json import json_dump_async, json_load_async
from commanderbot.lib.types import JsonObject

__all__ = (
    "SQLDatabaseAdapter",
    "JsonFileDatabaseAdapter",
    "SQLiteDatabaseAdapter",
)


CacheType = TypeVar("CacheType")


class SQLDatabaseAdapter(Protocol):
    """
    A protocol class for SQL databases
    """

    def connect(self) -> AsyncConnection:
        ...

    def begin(self) -> AsyncConnection:
        ...

    def session(self) -> AsyncSession:
        ...


@dataclass
class JsonFileDatabaseAdapter(Generic[CacheType]):
    """
    Wraps common operations for persistent data backed by a simple JSON file.

    Attributes
    ----------
    options
        Immutable, pre-defined settings that define core database behavior.
    serializer
        A callable that serializes Python objects into JSON objects.
    deserializer
        A callable that deserializes JSON objects into Python objects.
    log
        A logger named in a uniquely identifiable way.
    """

    options: JsonFileDatabaseOptions
    serializer: Callable[[CacheType], JsonObject]
    deserializer: Callable[[JsonObject], CacheType]

    log: Logger = field(init=False)

    # Lazily-initialized in-memory representation of state. The reason this is lazy is
    # because it needs to be asynchronously initialized from within an async method.
    # **Do not use this member; use `_get_cache()` instead.**
    __cache: Optional[CacheType] = field(init=False, default=None)

    # Lock used to avoid a potential race condition where multiple concurrent asyncio
    # tasks initialize the cache in parallel.
    __cache_lock = asyncio.Lock()

    def __post_init__(self):
        self.log = getLogger(
            f"{self.options.path.name} ({self.__class__.__name__}#{id(self)})"
        )

    async def _create_cache(self) -> CacheType:
        """Construct the initial cache from the database."""
        data = await self.read()
        assert isinstance(data, dict)
        return self.deserializer(data)

    async def get_cache(self) -> CacheType:
        """Create the cache if it doesn't already exist, and then return it."""
        async with self.__cache_lock:
            if self.__cache is None:
                self.log.info("Lazily-initializing new cache...")
                self.__cache = await self._create_cache()
        return self.__cache

    async def dirty(self):
        """Mark the cache as dirty, forcing a write to the database."""
        cache = await self.get_cache()
        data = self.serializer(cache)
        await self.write(data)

    async def read(self) -> JsonObject:
        """Read and return the data from the database file."""
        try:
            # Attempt to async load the file.
            return await json_load_async(self.options.path)
        except FileNotFoundError as ex:
            if self.options.no_init:
                # If the file doesn't exist, and we've been specifically told not to
                # automatically create it, then let the error fall through.
                raise ex
            else:
                # Otherwise, we can go ahead and automatically initialize the file.
                self.log.warning(
                    f"Initializing database file because it doesn't already exist: {self.options.path}"
                )
                # We need to have valid JSON in the file, so just use an empty object.
                await json_dump_async({}, self.options.path, mkdir=True)
                return {}

    async def write(self, data: JsonObject):
        """Write the given data to the database file."""
        await json_dump_async(data, self.options.path, indent=self.options.indent)  # type: ignore


@dataclass
class SQLiteDatabaseAdapter:
    """
    Wraps common operations for persistent data backed by a SQLite database.

    Attributes
    ----------
    options
        Immutable, pre-defined settings that define core database behavior.
    log
        A logger named in a uniquely identifiable way.
    engine
        The underlying SQLAlchemy engine object.
    """

    options: SQLiteDatabaseOptions

    log: Logger = field(init=False)
    engine: AsyncEngine = field(init=False)

    @property
    def path_or_in_memory(self) -> Optional[Path]:
        return self.options.path

    def __post_init__(self):
        if path := self.path_or_in_memory:
            self.log = getLogger(f"{path.name} ({self.__class__.__name__}#{id(self)})")
            self.log.info(f"Creating SQLite engine at: {path}")
            path_str = f"sqlite+aiosqlite:///{path}"
        else:
            self.log = getLogger(f"IN-MEMORY ({self.__class__.__name__}#{id(self)})")
            self.log.info("Creating IN-MEMORY SQLite engine")
            path_str = "sqlite://"
        self.engine = create_async_engine(path_str)

    def connect(self) -> AsyncConnection:
        return self.engine.connect()

    def begin(self) -> AsyncConnection:
        return self.engine.begin()

    def session(self) -> AsyncSession:
        return AsyncSession(self.engine)
