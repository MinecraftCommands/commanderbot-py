from dataclasses import dataclass
from typing import override

from discord import User

from commanderbot.ext.automod.event import AutomodEvent

__all__ = ("UserUpdated",)


@dataclass
class UserUpdated(AutomodEvent):
    before: User
    """The user's old info."""

    after: User
    """The user's updated info."""

    @property
    @override
    def actor(self) -> User:
        return self.after

    @property
    @override
    def user(self) -> User:
        return self.after
