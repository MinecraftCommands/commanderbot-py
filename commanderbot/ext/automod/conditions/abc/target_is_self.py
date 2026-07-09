from abc import abstractmethod
from typing import Optional, override

from discord import User

from commanderbot.ext.automod.automod_context import AutomodContext
from commanderbot.ext.automod.condition import AutomodCondition

__all__ = ("TargetIsSelf",)


class TargetIsSelf(AutomodCondition):
    @abstractmethod
    def get_target(self, context: AutomodContext) -> Optional[User]:
        pass

    @override
    async def check(self, context: AutomodContext) -> bool:
        if (user := self.get_target(context)) and (bot_user := context.bot.user):
            return user.id == bot_user.id
        return False
