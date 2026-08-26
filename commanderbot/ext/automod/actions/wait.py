import asyncio
from typing import Literal, override

from commanderbot.ext.automod.action import AutomodAction
from commanderbot.ext.automod.automod_context import AutomodContext
from commanderbot.lib.timedelta import Timedelta

__all__ = ("Wait",)


class Wait(AutomodAction):
    """
    Wait a certain amount of time before continuing.
    """

    type: Literal["wait"]

    delay: Timedelta
    """
    How long to wait for.
    """

    @override
    async def apply(self, context: AutomodContext):
        await asyncio.sleep(self.delay.total_seconds())
