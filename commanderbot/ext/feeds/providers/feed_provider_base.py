from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from logging import Logger, getLogger
from typing import Generic, Optional, Self, TypeVar
from urllib.parse import urlparse, urlunparse

from commanderbot.lib import FromDataMixin

__all__ = (
    "FeedProviderOptionsBase",
    "FeedProviderBase",
)

OptionsType = TypeVar("OptionsType")
CacheType = TypeVar("CacheType")


@dataclass
class FeedProviderOptionsBase(FromDataMixin):
    url: str
    icon_url: str


class FeedProviderBase(Generic[OptionsType, CacheType], ABC):
    """
    Base class for all feed providers
    """

    def __init__(self, url: str, logger_name: str):
        self.url: str = url

        parsed_url = urlparse(url)
        parsed_url = parsed_url._replace(path="", params="", query="", fragment="")
        self.base_url = urlunparse(parsed_url)

        self.prev_status_code: Optional[int] = None
        self.prev_request_date: Optional[datetime] = None
        self.next_request_date: Optional[datetime] = None

        self._log: Logger = getLogger(logger_name)
        self._cache: set[CacheType] = set()

    @classmethod
    @abstractmethod
    def from_options(cls, options: OptionsType) -> Self: ...

    @property
    def cached_items(self) -> int:
        return len(self._cache)

    def start(self):
        # Assumes that `self._on_poll` is a task from `discord.ext.tasks`
        self._log.info("Started polling!")
        self._on_poll.start()

    def stop(self):
        # Assumes that `self._on_poll` is a task from `discord.ext.tasks`
        self._log.info("Stopped polling!")
        self._on_poll.stop()

    def restart(self):
        # Assumes that `self._on_poll` is a task from `discord.ext.tasks`
        self._log.info("Restarting...")
        self._on_poll.restart()

    @abstractmethod
    async def _on_poll(self):
        """
        Poll the feed for new updates

        A subclass should override this and make it a task from `discord.ext.tasks`
        """
        ...
