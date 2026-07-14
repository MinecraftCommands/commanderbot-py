from typing import TYPE_CHECKING, Literal, override

from pydantic import Field

from commanderbot.ext.automod.automod_context import AutomodContext
from commanderbot.ext.automod.condition import AutomodCondition

__all__ = ("AllOf",)

if TYPE_CHECKING:
    from commanderbot.ext.automod.condition import AutomodConditionType


class AllOf(AutomodCondition):
    """
    Check if all sub-conditions pass (logical AND).
    """

    type: Literal["all_of"]

    conditions: list[AutomodConditionType] = Field(default_factory=list, min_length=1)
    """The sub-conditions to check."""

    @override
    async def check(self, context: AutomodContext) -> bool:
        for condition in self.conditions:
            if condition.disabled:
                continue
            if not await condition.check(context):
                return False
        return True
