from dataclasses import dataclass, field
from logging import Logger
from typing import TYPE_CHECKING, Any

from discord.ext.commands import Bot

from commanderbot.ext.automod.event import AutomodEvent

__all__ = ("AutomodContext",)

if TYPE_CHECKING:
    from commanderbot.ext.automod.automod_guild_state import AutomodGuildState
    from commanderbot.ext.automod.rule import AutomodRule


@dataclass
class AutomodContext:
    """
    The execution context that's given to all triggers, conditions, and actions.
    """

    bot: Bot
    log: Logger

    state: AutomodGuildState
    """The guild state that received the event."""

    rule: AutomodRule
    """The rule that's currently running."""

    event: AutomodEvent
    """The event that the rule is processing."""

    _metadata: dict[str, Any] = field(init=False, default_factory=dict)
    """Any additional data attached to the execution context."""

    def set_metadata(self, key: str, value: Any):
        """Add metadata to the execution context"""
        self._metadata[key] = value

    def remove_metadata(self, key: str):
        """Remove metadata from the execution context"""
        del self._metadata[key]
