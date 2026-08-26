from typing import Optional

from discord import Thread
from pydantic import BaseModel, ConfigDict, Field

from commanderbot.lib.predicates import is_category_channel, is_thread
from commanderbot.lib.types import ChannelID, GuildChannel, ThreadID

__all__ = ("ChannelsGuard",)


class ChannelsGuard(BaseModel):
    """
    Checks whether a channel matches a set of channels.
    """

    model_config = ConfigDict(use_attribute_docstrings=True)

    include: set[ChannelID | ThreadID] = Field(default_factory=set)
    """The channels to include. A channel will match if it's in this set."""

    exclude: set[ChannelID | ThreadID] = Field(default_factory=set)
    """The channels to exclude. A channel will match if it's not in this set."""

    def _ignore_by_includes(self, channel: GuildChannel | Thread) -> bool:
        if not self.include:
            return False

        # If the channel is a thread, check if its parent is included
        if is_thread(channel) and (parent := channel.parent):
            if parent.id in self.include:
                return False

        # Otherwise, ignore the channel if and only if it's not included
        return channel.id not in self.include

    def _ignore_by_excludes(self, channel: GuildChannel | Thread) -> bool:
        if not self.exclude:
            return False

        # If the channel is a thread, check if its parent is excluded
        if is_thread(channel) and (parent := channel.parent):
            if parent.id in self.exclude:
                return False

        # Otherwise, ignore the channel if and only if it's excluded
        return channel.id in self.exclude

    def ignore(self, channel: Optional[GuildChannel | Thread]) -> bool:
        """Determine whether to ignore the channel."""
        if not channel:
            return False

        # Skip checking category channels
        if is_category_channel(channel):
            return False

        return self._ignore_by_includes(channel) or self._ignore_by_excludes(channel)
