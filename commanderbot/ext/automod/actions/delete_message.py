from typing import Literal, override

from commanderbot.ext.automod.action import AutomodAction
from commanderbot.ext.automod.automod_context import AutomodContext

__all__ = ("DeleteMessage",)


class DeleteMessage(AutomodAction):
    """
    Delete the message in context.
    """

    type: Literal["delete_message"]

    @override
    async def apply(self, context: AutomodContext):
        if message := context.event.message:
            await message.delete()
