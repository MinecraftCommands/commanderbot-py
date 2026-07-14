import random
from typing import Literal, override

from pydantic import Field

from commanderbot.ext.automod.automod_context import AutomodContext
from commanderbot.ext.automod.condition import AutomodCondition

__all__ = ("RandomChance",)


class RandomChance(AutomodCondition):
    """
    Generate a random number between `0.0` and `1.0` and check if it's below `chance`.
    """

    type: Literal["random_chance"]

    chance: float = Field(ge=0.0, le=1.0)
    """A number between `0.0` and `1.0` (inclusive)."""

    @override
    async def check(self, context: AutomodContext) -> bool:
        return random.random() < self.chance
