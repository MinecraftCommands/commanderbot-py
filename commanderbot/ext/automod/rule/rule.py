from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from commanderbot.ext.automod.action import AutomodActionType
from commanderbot.ext.automod.automod_context import AutomodContext
from commanderbot.ext.automod.condition import AutomodConditionType
from commanderbot.ext.automod.trigger import AutomodTriggerType
from commanderbot.lib.log_channel import LogChannel

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

    log: Optional[LogChannel] = None
    """Override the log channel for this rule."""

    triggers: list[AutomodTriggerType] = Field(min_length=1)
    """A list of triggers that cause the rule to run."""

    conditions: list[AutomodConditionType] = Field(default_factory=list)
    """A list of conditions that must *all* pass for the actions to run."""

    actions: list[AutomodActionType] = Field(min_length=1)
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

    def __hash__(self) -> int:
        return hash((self.__class__, self.name))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, AutomodRule):
            return False
        return self.name == other.name


# We need to rebuild the model because the conditions and actions have circular references
AutomodRule.model_rebuild()
