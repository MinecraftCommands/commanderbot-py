from typing import Literal, override

from commanderbot.ext.automod.automod_context import AutomodContext
from commanderbot.ext.automod.condition import AutomodCondition

__all__ = ("ReturnTrue",)


class ReturnTrue(AutomodCondition):
    """
    A condition that is always true.
    """

    type: Literal["return_true"] = "return_true"

    @override
    async def check(self, context: AutomodContext) -> bool:
        return True
