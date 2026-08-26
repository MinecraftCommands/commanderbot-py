from typing import Literal, override

from commanderbot.ext.automod.action import AutomodAction
from commanderbot.ext.automod.automod_context import AutomodContext
from commanderbot.ext.automod.automod_exceptions import AutomodException

__all__ = ("ThrowError",)


class ThrowError(AutomodAction):
    """
    Throw an error when running the action.

    Intended for testing and debugging.
    """

    type: Literal["throw_error"]

    error: str
    """A human-readable error message."""

    @override
    async def apply(self, context: AutomodContext):
        raise AutomodException(self.error)
