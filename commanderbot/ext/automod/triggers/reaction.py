from typing import Literal, Optional, override

from commanderbot.ext.automod import events
from commanderbot.ext.automod.event import AutomodEvent
from commanderbot.ext.automod.guards import (
    CategoriesGuard,
    ChannelsGuard,
    ChannelTypesGuard,
    ReactionsGuard,
    RolesGuard,
)
from commanderbot.ext.automod.types import AutomodRuleRef
from commanderbot.ext.automod.trigger import AutomodTrigger

__all__ = ("Reaction",)


class Reaction(AutomodTrigger):
    """
    Triggers when a member reacts to a message.
    """

    type: Literal["reaction"] = "reaction"
    event_types = (events.ReactionAdded, events.ReactionRemoved)

    reactions: Optional[ReactionsGuard] = None
    """The reactions to match against. If empty, all reactions will match."""

    categories: Optional[CategoriesGuard] = None
    """The categories to match against. If empty, all categories will match."""

    channel_types: Optional[ChannelTypesGuard] = None
    """The channel types to match against. If empty, all channel types will match."""

    channels: Optional[ChannelsGuard] = None
    """The channels to match against. If empty, all channels will match."""

    author_roles: Optional[RolesGuard] = None
    """The author roles to match against. If empty, all roles will match."""

    actor_roles: Optional[RolesGuard] = None
    """The actor roles to match against. If empty, all roles will match."""

    @override
    async def ignore(self, rule: AutomodRuleRef, event: AutomodEvent) -> bool:
        assert isinstance(event, (events.ReactionAdded, events.ReactionRemoved))

        if self.reactions and self.reactions.ignore(event.reaction):
            return True

        if self.categories and self.categories.ignore(event.category):
            return True

        if self.channel_types and self.channel_types.ignore(event.channel):
            return True

        if self.channels and self.channels.ignore(event.channel):
            return True

        if self.author_roles and self.author_roles.ignore(event.author):
            return True

        if self.actor_roles and self.actor_roles.ignore(event.actor):
            return True

        return False
