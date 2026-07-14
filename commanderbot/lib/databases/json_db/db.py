import asyncio
from dataclasses import dataclass, field
from logging import Logger, getLogger
from pathlib import Path
from typing import Optional

from pydantic import BaseModel

from .config import JsonDBOptions, is_json_file_options


@dataclass
class JsonDB[CacheType: BaseModel]:
    """
    Wraps common operations for persistent data backed by a simple JSON file.

    Attributes
    ----------
    options
        Immutable, pre-defined settings that define core database behavior.
    cache_cls
        A type that inherits from `pydantic.BaseModel` which will be used for
        initializing the cache.
    log
        A logger named in a uniquely identifiable way.
    """

    options: JsonDBOptions
    cache_cls: type[CacheType]
    log: Logger = field(init=False)

    __cache: Optional[CacheType] = field(init=False, default=None)
    """
    Lazily-initialized in-memory representation of state. The reason this is lazy is
    because it needs to be asynchronously initialized from within an async method.
    **Do not use this member; use `get_cache()` instead.**
    """

    __cache_lock = asyncio.Lock()
    """
    Lock used to avoid potential race conditions where multiple concurrent asyncio
    tasks initialize the cache or write it to the database file.
    """

    def __post_init__(self):
        if is_json_file_options(self.options):
            self.log = getLogger(
                f"{self.options.path.name} ({self.__class__.__name__}#{id(self)})"
            )
        else:
            self.log = getLogger(f":memory: ({self.__class__.__name__}#{id(self)})")

    def _read(self) -> str:
        """
        Read and return the data from the database file.
        """
        assert is_json_file_options(self.options)
        path: Path = self.options.path
        try:
            # Attempt read the file.
            return self.options.path.read_text(encoding="utf-8")
        except FileNotFoundError as ex:
            if self.options.no_init:
                # If the file doesn't exist, and we've been specifically told not to
                # automatically create it, then let the error fall through.
                raise ex
            else:
                # Otherwise, we can go ahead and automatically initialize the file.
                self.log.warning(
                    f"Initializing database file because it doesn't already exist: {path}"
                )
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("{}", encoding="utf-8")
                return "{}"

    def _write(self, data: str):
        """
        Write the given data to the database file.
        """
        assert is_json_file_options(self.options)
        self.options.path.write_text(data, encoding="utf-8")

    async def get_cache(self) -> CacheType:
        """
        Create the cache if it doesn't already exist, and then return it.
        """
        async with self.__cache_lock:
            if self.__cache is None:
                self.log.info("Lazily-initializing new cache...")
                if is_json_file_options(self.options):
                    data: str = await asyncio.to_thread(self._read)
                    self.__cache = self.cache_cls.model_validate_json(data)
                else:
                    self.__cache = self.cache_cls()
        return self.__cache

    async def commit(self):
        """
        Commit any changes to the cache, forcing a write to the database.
        """
        cache: CacheType = await self.get_cache()
        async with self.__cache_lock:
            if is_json_file_options(self.options):
                data: str = cache.model_dump_json(
                    indent=self.options.indent,
                    exclude_defaults=self.options.exclude_defaults,
                    exclude_none=self.options.exclude_none,
                )
                await asyncio.to_thread(self._write, data)
