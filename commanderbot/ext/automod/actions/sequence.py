from typing import TYPE_CHECKING, Literal, override

from pydantic import Field

from commanderbot.ext.automod.action import AutomodAction
from commanderbot.ext.automod.automod_context import AutomodContext

__all__ = ("Sequence",)

if TYPE_CHECKING:
    from commanderbot.ext.automod.action import AutomodActionType


class Sequence(AutomodAction):
    """
    Apply sub-actions in sequence.
    """

    type: Literal["sequence"]

    actions: list[AutomodActionType] = Field(min_length=1)
    """The sub-actions to apply."""

    @override
    async def apply(self, context: AutomodContext):
        for action in self.actions:
            if not action.disabled:
                await action.apply(context)
