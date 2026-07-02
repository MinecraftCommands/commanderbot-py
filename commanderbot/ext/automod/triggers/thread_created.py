from typing import Literal, Optional, override

from commanderbot.ext.automod import events
from commanderbot.ext.automod.automod_context import AutomodContext
from commanderbot.ext.automod.guards import (
    CategoriesGuard,
    ChannelsGuard,
    ChannelTypesGuard,
)
from commanderbot.ext.automod.trigger import AutomodTrigger

__all__ = ("ThreadCreated",)


class ThreadCreated(AutomodTrigger):
    """
    Triggers when a thread is created.
    """

    type: Literal["thread_created"] = "thread_created"
    event_types = (events.ThreadCreated,)

    parent_categories: Optional[CategoriesGuard] = None
    """The parent categories to match against. If empty, all parent categories will match."""

    parent_channel_types: Optional[ChannelTypesGuard] = None
    """The parent channel types to match against. If empty, all parent channel types will match."""

    parent_channels: Optional[ChannelsGuard] = None
    """The parent channels to match against. If empty, all channels will match."""

    @override
    async def ignore(self, context: AutomodContext) -> bool:
        assert isinstance(context.event, events.ThreadCreated)

        # The thread must have a parent
        parent = context.event.thread.parent
        if not parent:
            return True

        if self.parent_categories and self.parent_categories.ignore(parent.category):
            return True

        if self.parent_channel_types and self.parent_channel_types.ignore(parent):
            return True

        if self.parent_channels and self.parent_channels.ignore(parent):
            return True

        return False
