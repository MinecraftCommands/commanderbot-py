from typing import Literal, Optional, override

from commanderbot.ext.automod import events
from commanderbot.ext.automod.event import AutomodEvent
from commanderbot.ext.automod.guards import (
    CategoriesGuard,
    ChannelsGuard,
    ChannelTypesGuard,
)
from commanderbot.ext.automod.types import AutomodRuleRef
from commanderbot.ext.automod.trigger import AutomodTrigger

__all__ = ("ThreadDeleted",)


class ThreadDeleted(AutomodTrigger):
    """
    Triggers when a thread is deleted.
    """

    type: Literal["thread_deleted"] = "thread_deleted"
    event_types = (events.ThreadDeleted,)

    parent_categories: Optional[CategoriesGuard] = None
    """The parent categories to match against. If empty, all parent categories will match."""

    parent_channel_types: Optional[ChannelTypesGuard] = None
    """The parent channel types to match against. If empty, all parent channel types will match."""

    parent_channels: Optional[ChannelsGuard] = None
    """The parent channels to match against. If empty, all channels will match."""

    @override
    async def ignore(self, rule: AutomodRuleRef, event: AutomodEvent) -> bool:
        assert isinstance(event, events.ThreadDeleted)

        # The thread must have a parent
        parent = event.thread.parent
        if not parent:
            return True

        if self.parent_categories and self.parent_categories.ignore(parent.category):
            return True

        if self.parent_channel_types and self.parent_channel_types.ignore(parent):
            return True

        if self.parent_channels and self.parent_channels.ignore(parent):
            return True

        return False
