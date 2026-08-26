from typing import TYPE_CHECKING, Literal, override

from pydantic import Field, PositiveInt

from commanderbot.ext.automod.automod_context import AutomodContext
from commanderbot.ext.automod.condition import AutomodCondition

__all__ = ("AnyOf",)

if TYPE_CHECKING:
    from commanderbot.ext.automod.condition import AutomodConditionType


class AnyOf(AutomodCondition):
    """
    Check if a number of sub-conditions pass (logical OR).
    """

    type: Literal["any_of"]

    conditions: list[AutomodConditionType] = Field(min_length=1)
    """The sub-conditions to check."""

    count: PositiveInt = 1
    """
    The number of sub-conditions that must pass. If empty,
    only a single sub-condition is required to pass.
    """

    @override
    async def check(self, context: AutomodContext) -> bool:
        checks_passed: int = 0
        for condition in self.conditions:
            if condition.disabled:
                continue
            if await condition.check(context):
                checks_passed += 1
                if checks_passed == self.count:
                    return True
        return False
