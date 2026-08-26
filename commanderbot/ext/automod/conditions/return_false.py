from typing import Literal, override

from commanderbot.ext.automod.automod_context import AutomodContext
from commanderbot.ext.automod.condition import AutomodCondition

__all__ = ("ReturnFalse",)


class ReturnFalse(AutomodCondition):
    """
    A condition that is always false.
    """

    type: Literal["return_false"]

    @override
    async def check(self, context: AutomodContext) -> bool:
        return False
