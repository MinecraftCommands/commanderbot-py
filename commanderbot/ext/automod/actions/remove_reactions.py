from typing import Literal, override

from pydantic import Field

from commanderbot.ext.automod.action import AutomodAction
from commanderbot.ext.automod.automod_context import AutomodContext

__all__ = ("RemoveReactions",)


class RemoveReactions(AutomodAction):
    """
    Remove certain reactions from the message in context.
    """

    type: Literal["remove_reactions"]

    reactions: set[str] = Field(default_factory=set, min_length=1)
    """The reactions to remove."""

    @override
    async def apply(self, context: AutomodContext):
        if message := context.event.message:
            for reaction in self.reactions:
                await message.clear_reaction(reaction)

