from dataclasses import dataclass, field
from logging import Logger, getLogger
from typing import Callable, Generic, Iterable, TypeVar

from discord import Guild
from discord.ext.commands import Bot, Cog

from commanderbot.lib.predicates import is_guild
from commanderbot.lib.types import GuildID

__all__ = (
    "CogState",
    "CogGuildState",
    "CogGuildStateManager",
    "GuildPartitionedCogState",
)


@dataclass
class CogState:
    """
    Encapsulates the state and logic of a particular cog.

    This is intended to be used as a starting point for a class that separates the cog's
    in-memory/persistent state and business logic from its top-level definitions, such
    as event listeners and command definitions.

    Attributes
    -----------
    bot
        The bot/client instance the cog is attached to.
    cog
        The cog instance this state is attached to.
    log
        A logger named in a uniquely identifiable way.
    """

    bot: Bot
    cog: Cog

    log: Logger = field(init=False)

    def __post_init__(self):
        self.log = getLogger(
            f"{self.cog.qualified_name} ({self.__class__.__name__}#{id(self)})"
        )


@dataclass
class CogGuildState:
    """
    Encapsulates the state and logic of a particular cog, at the guild level.

    This is a thin abstraction that affords us two main conveniences:
    1. keeping guild-based logic separate from global logic; and
    2. keeping the state of each guild isolated from one another.

    Attributes
    -----------
    bot
        The bot/client instance the cog is attached to.
    cog
        The cog instance this state is attached to.
    guild
        The guild instance being managed.
    log
        A logger named in a uniquely identifiable way.
    """

    bot: Bot
    cog: Cog
    guild: Guild

    log: Logger = field(init=False)

    def __post_init__(self):
        self.log = getLogger(
            f"{self.cog.qualified_name}@{self.guild}"
            + f" ({self.__class__.__name__}#{id(self)})"
        )


GuildStateType = TypeVar("GuildStateType", bound=CogGuildState)


@dataclass
class CogGuildStateManager(Generic[GuildStateType]):
    """
    A glorified dictionary that handles the lazy-initialization of guild states.

    Attributes
    ----------
    bot
        The bot/client instance the cog is attached to.
    cog
        The cog instance this state is attached to.
    factory
        A callable object that creates new guild states.

        There are several ways to provide such an object:
        1. a lambda, function, or bound method with a matching signature; or
        2. an instance of a class that implements `__call__` with a matching signature.
    log
        A logger named in a uniquely identifiable way.
    """

    bot: Bot
    cog: Cog
    factory: Callable[[Guild], GuildStateType]

    log: Logger = field(init=False)

    _state_by_id: dict[GuildID, GuildStateType] = field(init=False)

    def __post_init__(self):
        self.log = getLogger(
            f"{self.cog.qualified_name} ({self.__class__.__name__}#{id(self)})"
        )
        self._state_by_id = {}

    def __getitem__(self, key: Guild | GuildID) -> GuildStateType:
        return self.get(key)

    @property
    def available(self) -> Iterable[GuildStateType]:
        yield from self._state_by_id.values()

    def _set_state(self, guild: Guild, state: GuildStateType):
        self.log.debug(f"Setting state for guild: {guild}")
        if guild.id in self._state_by_id:
            raise KeyError(f"Attempted to overwrite state for guild: {guild}")
        self._state_by_id[guild.id] = state

    def _init_state(self, guild: Guild) -> GuildStateType:
        self.log.debug(f"Initializing state for guild: {guild}")
        guild_state = self.factory(guild)
        self._set_state(guild, guild_state)
        return guild_state

    def get(self, key: Guild | GuildID) -> GuildStateType:
        # Lazily-initialize guild states as they are accessed.
        guild = key if is_guild(key) else self.bot.get_guild(key)
        if not guild:
            raise ValueError(f"Unable to initialize state for unknown guild: {key}")
        guild_state = self._state_by_id.get(guild.id)
        if guild_state is None:
            guild_state = self._init_state(guild)
        return guild_state


@dataclass
class GuildPartitionedCogState(CogState, Generic[GuildStateType]):
    """
    Encapsulates the state and logic of a particular cog, for each guild.

    This is intended to be used just as `CogState` is, but in addition to maintaining
    several sub-states that each correspond to their own guild. A subclass of
    `CogGuildState` should be defined to implement guild-specific functionality.

    Uses a `CogGuildStateManager` to manage the lazy-initialization of `CogGuildState`
    instances, and implements `__getitem__` as a shortcut to this.

    Attributes
    -----------
    bot
        The bot/client instance the cog is attached to.
    cog
        The cog instance this state is attached to.
    log
        A logger named in a uniquely identifiable way.
    guilds
        The `CogGuildStateManager` instance to manage guild states.
    """

    guilds: CogGuildStateManager[GuildStateType]

    def __getitem__(self, key: Guild | GuildID) -> GuildStateType:
        return self.guilds[key]
