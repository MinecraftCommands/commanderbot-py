from typing import Optional

import discord
from discord import Thread
from pydantic import BaseModel, ConfigDict, Field

from commanderbot.lib.enums import ChannelType
from commanderbot.lib.types import GuildChannel

__all__ = ("ChannelTypesGuard",)


class ChannelTypesGuard(BaseModel):
    """
    Checks whether a channel has a certain type.
    """

    model_config = ConfigDict(use_attribute_docstrings=True)

    include: set[ChannelType] = Field(default_factory=set)
    """The channel types to include. A channel will match if it's one of these types."""

    exclude: set[ChannelType] = Field(default_factory=set)
    """The channel types to exclude. A channel will match if it's not one of these types."""

    def _ignore_by_includes(self, channel_type: discord.ChannelType) -> bool:
        if self.include:
            return channel_type not in self.include
        return False

    def _ignore_by_excludes(self, channel_type: discord.ChannelType) -> bool:
        if self.exclude:
            return channel_type in self.exclude
        return False

    def ignore(self, channel: Optional[GuildChannel | Thread]) -> bool:
        """Determine whether to ignore the channel based on its type."""
        if not channel:
            return False

        return self._ignore_by_includes(channel.type) or self._ignore_by_excludes(
            channel.type
        )
