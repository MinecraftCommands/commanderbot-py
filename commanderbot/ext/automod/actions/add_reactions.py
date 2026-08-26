from typing import Literal, override

from pydantic import Field

from commanderbot.ext.automod.action import AutomodAction
from commanderbot.ext.automod.automod_context import AutomodContext

__all__ = ("AddReactions",)


class AddReactions(AutomodAction):
    """
    Add reactions to the message in context.
    """

    type: Literal["add_reactions"]

    reactions: set[str] = Field(min_length=1)
    """The reactions to add."""

    @override
    async def apply(self, context: AutomodContext):
        if message := context.event.message:
            for reaction in self.reactions:
                await message.add_reaction(reaction)
