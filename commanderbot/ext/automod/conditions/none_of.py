from dataclasses import dataclass
from typing import Type, TypeVar

from commanderbot.ext.automod.automod_condition import (
    AutomodCondition,
    AutomodConditionBase,
    deserialize_conditions,
)
from commanderbot.ext.automod.automod_event import AutomodEvent
from commanderbot.lib import JsonObject

ST = TypeVar("ST")


@dataclass
class NoneOf(AutomodConditionBase):
    """
    Passes if and only if none of the sub-conditions pass.

    Attributes
    ----------
    conditions
        The sub-conditions to check.
    """

    conditions: tuple[AutomodCondition]

    @classmethod
    def from_data(cls: Type[ST], data: JsonObject) -> ST:
        raw_conditions = data["conditions"]
        conditions = deserialize_conditions(raw_conditions)
        return cls(
            description=data.get("description"),
            conditions=conditions,
        )

    async def check(self, event: AutomodEvent) -> bool:
        for condition in self.conditions:
            if await condition.check(event):
                return False
        return True


def create_condition(data: JsonObject) -> AutomodCondition:
    return NoneOf.from_data(data)
