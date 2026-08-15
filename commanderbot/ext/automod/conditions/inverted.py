from typing import TYPE_CHECKING, Literal, override

from commanderbot.ext.automod.automod_context import AutomodContext
from commanderbot.ext.automod.condition import AutomodCondition

if TYPE_CHECKING:
    from commanderbot.ext.automod.condition import AutomodConditionType

__all__ = ("Inverted",)


class Inverted(AutomodCondition):
    """
    Inverts the result of a sub-condition.
    """

    type: Literal["inverted"]

    condition: AutomodConditionType
    """The sub-condition to check."""

    @override
    async def check(self, context: AutomodContext) -> bool:
        return not await self.condition.check(context)
