from dataclasses import dataclass, field
from typing import Any

from commanderbot.ext.automod.event import AutomodEvent
from commanderbot.ext.automod.types import AutomodRuleRef

__all__ = ("AutomodContext",)


@dataclass
class AutomodContext:
    """
    The execution context that's given to all triggers, conditions, and actions.
    """

    rule: AutomodRuleRef
    """The rule that's currently running."""

    event: AutomodEvent
    """The event the rule is processing."""

    _metadata: dict[str, Any] = field(init=False, default_factory=dict)
    """Any additional data attached to the execution context."""

    def set_metadata(self, key: str, value: Any):
        """Add metadata to the execution context"""
        self._metadata[key] = value

    def remove_metadata(self, key: str):
        """Remove metadata from the execution context"""
        del self._metadata[key]
