from abc import ABC
from dataclasses import dataclass
from logging import Logger
from typing import Optional

from discord import CategoryChannel, Member, Message, Reaction, Thread, User
from discord.ext.commands import Bot

from commanderbot.ext.automod.types import AutomodGuildStateRef
from commanderbot.lib.predicates import is_thread
from commanderbot.lib.types import GuildChannel

__all__ = ("AutomodEvent",)


@dataclass
class AutomodEvent(ABC):
    """
    Base class for all automod events.
    """

    state: AutomodGuildStateRef
    bot: Bot
    log: Logger

    @property
    def channel(self) -> Optional[GuildChannel | Thread]:
        """Return the relevant channel, if any."""
        return None

    @property
    def thread(self) -> Optional[Thread]:
        """Return the relevant thread, if any."""
        if is_thread(self.channel):
            return self.channel

    @property
    def category(self) -> Optional[CategoryChannel]:
        """Return the relevant category, if any."""
        if self.channel:
            return self.channel.category

    @property
    def message(self) -> Optional[Message]:
        """Return the relevant message, if any."""
        return None

    @property
    def reaction(self) -> Optional[Reaction]:
        """Return the relevant reaction, if any."""
        return None

    @property
    def author(self) -> Optional[Member | User]:
        """Return the relevant author, if any."""
        return None

    @property
    def actor(self) -> Optional[Member | User]:
        """Return the acting user, if any."""
        return None

    @property
    def member(self) -> Optional[Member]:
        """Return the member-in-question, if any."""
        return None

    @property
    def user(self) -> Optional[User]:
        """Return the user-in-question, if any."""
        return None
