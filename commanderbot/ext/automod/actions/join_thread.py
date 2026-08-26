from typing import Literal, override

from commanderbot.ext.automod.action import AutomodAction
from commanderbot.ext.automod.automod_context import AutomodContext

__all__ = ("JoinThread",)


class JoinThread(AutomodAction):
    """
    Make the bot join the thread in context.

    Even though bots receive events for threads, they are not listed as a member of the
    thread automatically. This can cause issues with sending messages.
    """

    type: Literal["join_thread"]

    @override
    async def apply(self, context: AutomodContext):
        if thread := context.event.thread:
            await thread.join()
