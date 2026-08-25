import asyncio
import random
from typing import Literal, Self, override

from pydantic import Field, PositiveFloat, model_validator

from commanderbot.ext.automod.action import AutomodAction
from commanderbot.ext.automod.automod_context import AutomodContext
from commanderbot.ext.automod.automod_exceptions import AutomodValidationError
from commanderbot.lib.predicates import is_messagable_guild_channel

__all__ = ("TypeInChannel",)


class TypeInChannel(AutomodAction):
    """
    Make the bot type in the channel in context for a certain amount of time.
    """

    type: Literal["type_in_channel"]

    min_time: PositiveFloat = Field(default=1)
    """The minimum amount of time to type for, in seconds. Defaults to 1 second."""

    max_time: PositiveFloat = Field(default=1, le=10)
    """The maximum amount of time to type for, in seconds. Defaults to 1 second."""

    @model_validator(mode="after")
    def _validate_model(self) -> Self:
        if self.min_time > self.max_time:
            raise AutomodValidationError("'min_time' is greater than 'max_time'")
        return self

    @override
    async def apply(self, context: AutomodContext):
        # We need to have a channel in context
        channel = context.event.channel
        if not channel:
            return

        # The channel must be messageable too
        if not is_messagable_guild_channel(channel):
            return

        # Type in the channel
        duration = random.uniform(self.min_time, self.max_time)
        async with channel.typing():
            await asyncio.sleep(duration)
