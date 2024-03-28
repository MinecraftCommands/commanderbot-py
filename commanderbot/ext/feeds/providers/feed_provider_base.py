from abc import ABC, abstractmethod
from collections import deque
from datetime import datetime
from logging import Logger, getLogger
from typing import Generic, Optional, Self, TypeVar

__all__ = ("FeedProviderBase",)

OptionsType = TypeVar("OptionsType")
CacheType = TypeVar("CacheType")


class FeedProviderBase(Generic[OptionsType, CacheType], ABC):
    """
    Base class for all feed providers
    """

    def __init__(self, url: str, icon_url: str, logger_name: str, cache_size: int):
        self.url: str = url
        self.icon_url: str = icon_url

        self.prev_status_code: Optional[int] = None
        self.prev_request_date: Optional[datetime] = None
        self.next_request_date: Optional[datetime] = None

        self._log: Logger = getLogger(logger_name)
        self._cache: deque[CacheType] = deque(maxlen=cache_size)
        self.cache_size: int = cache_size

    @classmethod
    @abstractmethod
    def from_options(cls, options: OptionsType) -> Self: ...

    @property
    def cached_items(self) -> int:
        return len(self._cache)

    @abstractmethod
    def start(self): ...

    @abstractmethod
    def stop(self): ...

    @abstractmethod
    def restart(self): ...
