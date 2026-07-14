import asyncio
from typing import Literal, override

from commanderbot.ext.automod.automod_context import AutomodContext
from commanderbot.ext.automod.condition import AutomodCondition
from commanderbot.lib.types import Timedelta

__all__ = ("Wait",)


class Wait(AutomodCondition):
    """
    Wait a certain amount of time before continuing.
    """

    type: Literal["wait"]

    delay: Timedelta
    """
    How long to wait for.
    """

    @override
    async def check(self, context: AutomodContext) -> bool:
        await asyncio.sleep(self.delay.total_seconds())
        return True
