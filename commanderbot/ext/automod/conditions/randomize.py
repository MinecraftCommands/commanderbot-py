import random
from typing import TYPE_CHECKING, Literal, Optional, override

from pydantic import BaseModel, ConfigDict, Field, PositiveInt

from commanderbot.ext.automod.automod_context import AutomodContext
from commanderbot.ext.automod.condition import AutomodCondition

__all__ = ("Randomize",)

if TYPE_CHECKING:
    from commanderbot.ext.automod.condition import AutomodConditionType


class WeightedCondition(BaseModel):
    """
    A sub-condition with an optional weight.
    """

    model_config = ConfigDict(use_attribute_docstrings=True)

    condition: AutomodConditionType
    """The sub-condition to check."""

    weight: PositiveInt = 1
    """The weight of the sub-condition. Defaults to `1`."""


class Randomize(AutomodCondition):
    """
    Check a random sub-condition.
    """

    type: Literal["randomize"]

    conditions: list[AutomodConditionType | WeightedCondition] = Field(min_length=1)
    """The sub-conditions to pick from."""

    def _roll(self) -> Optional[AutomodConditionType]:
        # Sum all the weights
        total_weight: int = 0
        for entry in self.conditions:
            if isinstance(entry, WeightedCondition):
                total_weight += entry.weight
            else:
                total_weight += 1

        # Pick a number between 0 and `total_weight`
        target_weight = random.randint(0, total_weight)

        # Get the first entry that causes `current_weight` to be
        # greater than or equal to `target_weight`
        current_weight: int = 0
        for entry in self.conditions:
            condition: Optional[AutomodConditionType] = None
            if isinstance(entry, WeightedCondition):
                condition = entry.condition
                current_weight += entry.weight
            else:
                condition = entry
                current_weight += 1

            if current_weight >= target_weight:
                return condition

    @override
    async def check(self, context: AutomodContext) -> bool:
        if (condition := self._roll()) and not condition.disabled:
            return await condition.check(context)
        return False
