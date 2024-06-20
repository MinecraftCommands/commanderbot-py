from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Any, Callable, Coroutine, Optional, TypeAlias

from discord.interactions import Interaction
from discord.ext.commands import Bot, Context

from commanderbot.core.command_tree import CachingCommandTree
from commanderbot.lib.event_data import EventData

EventErrorHandler: TypeAlias = Callable[
    [Exception, EventData, bool], Coroutine[Any, Any, Optional[bool]]
]

CommandErrorHandler: TypeAlias = Callable[
    [Exception, Context, bool], Coroutine[Any, Any, Optional[bool]]
]

AppCommandErrorHandler: TypeAlias = Callable[
    [Exception, Interaction, bool], Coroutine[Any, Any, Optional[bool]]
]


class CommanderBotBase(ABC, Bot):
    @property
    @abstractmethod
    def started_at(self) -> datetime:
        ...

    @property
    @abstractmethod
    def connected_since(self) -> datetime:
        ...

    @property
    @abstractmethod
    def uptime(self) -> timedelta:
        ...

    @property
    @abstractmethod
    def command_tree(self) -> CachingCommandTree:
        ...

    @abstractmethod
    def get_extension_options(self, ext_name: str) -> Optional[dict[str, Any]]:
        ...

    @abstractmethod
    def add_event_error_handler(self, handler: EventErrorHandler):
        ...

    @abstractmethod
    def add_command_error_handler(self, handler: CommandErrorHandler):
        ...

    @abstractmethod
    def add_app_command_error_handler(self, handler: AppCommandErrorHandler):
        ...
