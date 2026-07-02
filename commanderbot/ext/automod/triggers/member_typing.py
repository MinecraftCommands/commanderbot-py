from typing import Literal, Optional, override

from commanderbot.ext.automod import events
from commanderbot.ext.automod.automod_context import AutomodContext
from commanderbot.ext.automod.guards import (
    CategoriesGuard,
    ChannelsGuard,
    ChannelTypesGuard,
    RolesGuard,
)
from commanderbot.ext.automod.trigger import AutomodTrigger

__all__ = ("MemberTyping",)


class MemberTyping(AutomodTrigger):
    """
    Triggers when a user is typing.
    """

    type: Literal["member_typing"] = "member_typing"
    event_types = (events.MemberTyping,)

    categories: Optional[CategoriesGuard] = None
    """The categories to match against. If empty, all categories will match."""

    channel_types: Optional[ChannelTypesGuard] = None
    """The channel types to match against. If empty, all channel types will match."""

    channels: Optional[ChannelsGuard] = None
    """The channels to match against. If empty, all channels will match."""

    roles: Optional[RolesGuard] = None
    """The roles to match against. If empty, all roles will match."""

    @override
    async def ignore(self, context: AutomodContext) -> bool:
        assert isinstance(context.event, events.MemberTyping)

        if self.categories and self.categories.ignore(context.event.category):
            return True

        if self.channel_types and self.channel_types.ignore(context.event.channel):
            return True

        if self.channels and self.channels.ignore(context.event.channel):
            return True

        if self.roles and self.roles.ignore(context.event.member):
            return True

        return False
