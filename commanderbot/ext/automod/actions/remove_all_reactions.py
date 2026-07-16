from typing import Literal, override

from commanderbot.ext.automod.action import AutomodAction
from commanderbot.ext.automod.automod_context import AutomodContext

__all__ = ("RemoveAllReactions",)


class RemoveAllReactions(AutomodAction):
    """
    Remove all reactions from the message in context.
    """

    type: Literal["remove_all_reactions"]

    @override
    async def apply(self, context: AutomodContext):
        if message := context.event.message:
            await message.clear_reactions()
