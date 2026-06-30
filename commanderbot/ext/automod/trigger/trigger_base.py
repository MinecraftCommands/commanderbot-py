from abc import ABC
from typing import ClassVar, Optional

from pydantic import BaseModel, ConfigDict

from commanderbot.ext.automod.event import AutomodEvent
from commanderbot.ext.automod.types import AutomodRuleRef

__all__ = ("AutomodTrigger",)


class AutomodTrigger(ABC, BaseModel):
    """
    Base class for all automod triggers.

    Triggers specify which events they listen for and may have some configuration.
    """

    model_config = ConfigDict(use_attribute_docstrings=True)

    type: str
    """The trigger type."""

    description: Optional[str] = None
    """Describe what the trigger does."""

    disabled: Optional[bool] = None
    """Is the trigger disabled?"""

    event_types: ClassVar[tuple[type[AutomodEvent], ...]] = tuple()

    async def poll(self, rule: AutomodRuleRef, event: AutomodEvent) -> bool:
        """Checks whether an event activates the trigger."""

        # Skip event if the trigger is disabled
        if self.disabled:
            return False

        # Skip event if it's not an event we're listening for
        event_type = type(event)
        if event_type not in self.event_types:
            return False

        # Skip event if it should be ignored
        if await self.ignore(rule, event):
            return False

        # We probably care about the event if we got this far
        return True

    async def ignore(self, rule: AutomodRuleRef, event: AutomodEvent) -> bool:
        """Override this if more than just the event type needs to be checked."""
        return False
