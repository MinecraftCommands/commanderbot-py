from typing import Literal, Optional, override

from commanderbot.ext.automod import events
from commanderbot.ext.automod.event import AutomodEvent
from commanderbot.ext.automod.guards import (
    CategoriesGuard,
    ChannelsGuard,
    ChannelTypesGuard,
    DiscordAutomodRulesGuard,
    RolesGuard,
)
from commanderbot.ext.automod.trigger import AutomodTrigger
from commanderbot.ext.automod.types import AutomodRuleRef

__all__ = ("DiscordAutomodBlockedMessage",)


class DiscordAutomodBlockedMessage(AutomodTrigger):
    """
    Triggers when Discord's automod blocks a message.
    """

    type: Literal["discord_automod_blocked_message"] = "discord_automod_blocked_message"
    event_types = (events.DiscordAutomodBlockedMessage,)

    rules: Optional[DiscordAutomodRulesGuard] = None
    """The Discord automod rules to match against. If empty, all rules will match."""

    categories: Optional[CategoriesGuard] = None
    """The categories to match against. If empty, all categories will match."""

    channel_types: Optional[ChannelTypesGuard] = None
    """The channel types to match against. If empty, all channel types will match."""

    channels: Optional[ChannelsGuard] = None
    """The channels to match against. If empty, all channels will match."""

    author_roles: Optional[RolesGuard] = None
    """The author roles to match against. If empty, all roles will match."""

    @override
    async def ignore(self, rule: AutomodRuleRef, event: AutomodEvent) -> bool:
        assert isinstance(event, events.DiscordAutomodBlockedMessage)

        if self.rules and self.rules.ignore(event.rule_id):
            return True

        if self.categories and self.categories.ignore(event.category):
            return True

        if self.channel_types and self.channel_types.ignore(event.channel):
            return True

        if self.channels and self.channels.ignore(event.channel):
            return True

        if self.author_roles and self.author_roles.ignore(event.author):
            return True

        return False
