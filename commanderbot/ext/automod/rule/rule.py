from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from commanderbot.ext.automod.action import AutomodActionType
from commanderbot.ext.automod.automod_context import AutomodContext
from commanderbot.ext.automod.condition import AutomodConditionType
from commanderbot.ext.automod.trigger import AutomodTriggerType

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

    triggers: list[AutomodTriggerType] = Field(default_factory=list, min_length=1)
    """A list of triggers that cause the rule to run."""

    conditions: list[AutomodConditionType] = Field(default_factory=list)
    """A list of conditions that must *all* pass for the actions to run."""

    actions: list[AutomodActionType] = Field(default_factory=list, min_length=1)
    """A list of actions that will all run if the conditions pass."""

    async def _poll_triggers(self, context: AutomodContext) -> bool:
        for trigger in self.triggers:
            if trigger.disabled:
                continue
            if await trigger.poll(context):
                return True
        return False

    async def _check_conditions(self, context: AutomodContext) -> bool:
        for condition in self.conditions:
            if condition.disabled:
                continue
            if not await condition.check(context):
                return False
        return True

    async def _apply_actions(self, context: AutomodContext):
        for action in self.actions:
            if action.disabled:
                continue
            await action.apply(context)

    async def run(self, context: AutomodContext) -> bool:
        if self.disabled:
            return False

        if not await self._poll_triggers(context):
            return False

        if not await self._check_conditions(context):
            return False

        await self._apply_actions(context)
        return True


# We need to rebuild the model because the conditions and actions have circular references
AutomodRule.model_rebuild()
