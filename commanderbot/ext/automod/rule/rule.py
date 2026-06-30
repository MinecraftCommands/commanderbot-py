from typing import Optional

from pydantic import BaseModel, ConfigDict

from commanderbot.ext.automod.event import AutomodEvent
from commanderbot.ext.automod.trigger import AutomodTriggerCollection

__all__ = ("AutomodRule",)


class AutomodRule(BaseModel):
    """
    An automod rule details how to perform an automated task.
    """

    model_config = ConfigDict(use_attribute_docstrings=True)

    name: str
    """The name of the rule."""

    description: Optional[str] = None
    """Describe what the rule does."""

    disabled: Optional[bool] = None
    """Is the rule disabled?"""

    triggers: AutomodTriggerCollection
    """A list of triggers that cause the rule to run."""

    async def _poll_triggers(self, event: AutomodEvent) -> bool:
        for trigger in self.triggers:
            if await trigger.poll(self, event):
                return True
        return False

    async def run(self, event: AutomodEvent) -> bool:
        if self.disabled:
            return False

        if await self._poll_triggers(event):
            return True

        return False
