from typing import Optional

from pydantic import BaseModel, ConfigDict

from commanderbot.ext.automod.event import AutomodEvent
from commanderbot.ext.automod.automod_context import AutomodContext
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

    async def _poll_triggers(self, context: AutomodContext) -> bool:
        for trigger in self.triggers:
            if await trigger.poll(context):
                return True
        return False

    async def _check_conditions(self, context: AutomodContext) -> bool:
        return True

    async def _apply_actions(self, context: AutomodContext):
        return

    async def run(self, event: AutomodEvent) -> bool:
        if self.disabled:
            return False

        context = AutomodContext(self, event)
        if not await self._poll_triggers(context):
            return False

        if not self._check_conditions(context):
            return False

        await self._apply_actions(context)
        return True
