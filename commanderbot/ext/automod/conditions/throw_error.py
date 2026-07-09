from typing import Literal, override

from commanderbot.ext.automod.automod_context import AutomodContext
from commanderbot.ext.automod.condition import AutomodCondition

__all__ = ("ThrowError",)


class ThrowError(AutomodCondition):
    """
    Throw an error when checking the condition.
    """

    type: Literal["throw_error"] = "throw_error"

    error: str
    """A human-readable error message."""

    @override
    async def check(self, context: AutomodContext) -> bool:
        raise Exception(self.error)
