import random
from typing import TYPE_CHECKING, Literal, Optional, override

from pydantic import BaseModel, ConfigDict, Field, PositiveInt

from commanderbot.ext.automod.action import AutomodAction
from commanderbot.ext.automod.automod_context import AutomodContext

__all__ = ("Randomize",)

if TYPE_CHECKING:
    from commanderbot.ext.automod.action import AutomodActionType


class WeightedAction(BaseModel):
    """
    A sub-action with an optional weight.
    """

    model_config = ConfigDict(use_attribute_docstrings=True)

    action: Optional[AutomodActionType] = None
    """The sub-action to apply."""

    weight: PositiveInt = 1
    """The weight of the sub-action. Defaults to `1`."""


class Randomize(AutomodAction):
    """
    Apply a random sub-action.
    """

    type: Literal["randomize"]

    actions: list[AutomodActionType | WeightedAction] = Field(
        default_factory=list, min_length=1
    )
    """The sub-actions to pick from."""

    def _roll(self) -> Optional[AutomodActionType]:
        # Sum all the weights
        total_weight: int = 0
        for entry in self.actions:
            if isinstance(entry, WeightedAction):
                total_weight += entry.weight
            else:
                total_weight += 1

        # Pick a number between 0 and `total_weight`
        target_weight = random.randint(0, total_weight)

        # Get the first entry that causes `current_weight` to be
        # greater than or equal to `target_weight`
        current_weight: int = 0
        for entry in self.actions:
            action: Optional[AutomodActionType] = None
            if isinstance(entry, WeightedAction):
                action = entry.action
                current_weight += entry.weight
            else:
                action = entry
                current_weight += 1

            if current_weight >= target_weight:
                return action

    @override
    async def apply(self, context: AutomodContext):
        if (action := self._roll()) and not action.disabled:
            await action.apply(context)
