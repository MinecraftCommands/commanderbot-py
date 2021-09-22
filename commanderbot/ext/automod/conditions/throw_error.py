from dataclasses import dataclass

from commanderbot.ext.automod.automod_event import AutomodEvent
from commanderbot.ext.automod.condition import Condition, ConditionBase
from commanderbot.lib import JsonObject


@dataclass
class ThrowError(ConditionBase):
    """
    Throw an error when checking the condition.

    Intended for testing and debugging.

    Attributes
    ----------
    error
        A human-readable error message.
    """

    error: str

    async def check(self, event: AutomodEvent) -> bool:
        raise Exception(self.error)


def create_condition(data: JsonObject) -> Condition:
    return ThrowError.from_data(data)
