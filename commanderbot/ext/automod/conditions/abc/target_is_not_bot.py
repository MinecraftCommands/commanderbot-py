from abc import abstractmethod
from typing import Optional, override

from discord import User

from commanderbot.ext.automod.automod_context import AutomodContext
from commanderbot.ext.automod.condition import AutomodCondition

__all__ = ("TargetIsNotBot",)


class TargetIsNotBot(AutomodCondition):
    @abstractmethod
    def get_target(self, context: AutomodContext) -> Optional[User]:
        ...

    @override
    async def check(self, context: AutomodContext) -> bool:
        if user := self.get_target(context):
            return not user.bot
        return True
