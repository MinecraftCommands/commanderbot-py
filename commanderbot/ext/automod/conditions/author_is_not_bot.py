from dataclasses import dataclass
from typing import Any, Optional, TypeVar

from discord import Member

from commanderbot.ext.automod.automod_event import AutomodEvent
from commanderbot.ext.automod.condition import Condition
from commanderbot.ext.automod.conditions.abc.target_is_not_bot_base import (
    TargetIsNotBotBase,
)

ST = TypeVar("ST")


@dataclass
class AuthorIsNotBot(TargetIsNotBotBase):
    """
    Check if the author in context is not a bot.
    """

    def get_target(self, event: AutomodEvent) -> Optional[Member]:
        return event.author


def create_condition(data: Any) -> Condition:
    return AuthorIsNotBot.from_data(data)
