from typing import Literal, Optional, override

from discord import Member, Role, User

from commanderbot.ext.automod import events
from commanderbot.ext.automod.event import AutomodEvent
from commanderbot.ext.automod.guards import (
    CategoriesGuard,
    ChannelsGuard,
    ChannelTypesGuard,
    RolesGuard,
)
from commanderbot.ext.automod.types import AutomodRuleRef
from commanderbot.ext.automod.trigger import AutomodTrigger

__all__ = ("MentionsRemovedFromMessage",)


class MentionsRemovedFromMessage(AutomodTrigger):
    """
    Triggers when a message with mentions is edited or deleted.

    This can be used for detecting suspected ghost pings.
    """

    type: Literal["mentions_removed_from_message"] = "mentions_removed_from_message"
    event_types = (events.MessageEdited, events.MessageDeleted)

    categories: Optional[CategoriesGuard] = None
    """The categories to match against. If empty, all categories will match."""

    channel_types: Optional[ChannelTypesGuard] = None
    """The channel types to match against. If empty, all channel types will match."""

    channels: Optional[ChannelsGuard] = None
    """The channels to match against. If empty, all channels will match."""

    author_roles: Optional[RolesGuard] = None
    """The author roles to match against. If empty, all roles will match."""

    victim_roles: Optional[RolesGuard] = None
    """The victim roles to match against. If empty, all roles will match."""

    victim_user_roles: Optional[RolesGuard] = None
    """The roles of the victim users to match against. If empty, all roles will match."""

    @override
    async def ignore(self, rule: AutomodRuleRef, event: AutomodEvent) -> bool:
        assert isinstance(event, (events.MessageEdited, events.MessageDeleted))

        if self.categories and self.categories.ignore(event.category):
            return True

        if self.channel_types and self.channel_types.ignore(event.channel):
            return True

        if self.channels and self.channels.ignore(event.channel):
            return True

        if self.author_roles and self.author_roles.ignore(event.author):
            return True

        removed_user_mentions: set[User | Member] = set()
        removed_role_mentions: set[Role] = set()
        match event:
            # If the message was edited, check for mentions that were removed
            case events.MessageEdited():
                # Check for removed user mentions
                after_user_mention_ids = {user.id for user in event.after.mentions}
                for before_user_mention in event.before.mentions:
                    if before_user_mention.id not in after_user_mention_ids:
                        removed_user_mentions.add(before_user_mention)

                # Check for removed role mentions
                after_role_mention_ids = {role.id for role in event.after.role_mentions}
                for before_role_mention in event.before.role_mentions:
                    if before_role_mention.id not in after_role_mention_ids:
                        removed_role_mentions.add(before_role_mention)

            # If the message was deleted, get any mentions at all
            case events.MessageDeleted():
                # Get removed user mentions
                for user_mention in event.message.mentions:
                    removed_user_mentions.add(user_mention)

                # Get removed role mentions
                for role_mention in event.message.role_mentions:
                    removed_role_mentions.add(role_mention)

        # Remove the author's own mention
        if event.author in removed_user_mentions:
            removed_user_mentions.remove(event.author)

        # Remove any excluded mentions
        if self.victim_user_roles:
            removed_user_mentions = {
                user
                for user in removed_user_mentions
                if self.victim_user_roles.member_matches(user)
            }

        if self.victim_roles:
            removed_role_mentions = {
                role
                for role in removed_role_mentions
                if self.victim_roles.role_matches(role)
            }

        # Ignore event if we have no mentions at all
        removed_mentions: list[Role | User | Member] = [
            *removed_role_mentions,
            *removed_user_mentions,
        ]
        if not removed_mentions:
            return True

        # Add removed mentions fields to event
        event.set_metadata(
            rule.name,
            "removed_mentions",
            " ".join((m.mention for m in removed_mentions)),
        )
        event.set_metadata(
            rule.name,
            "removed_mention_names",
            " ".join((f"`{m}`" for m in removed_mentions)),
        )

        # Add removed user mentions fields to event
        if removed_user_mentions:
            event.set_metadata(
                rule.name,
                "removed_user_mentions",
                " ".join((m.mention for m in removed_user_mentions)),
            )
            event.set_metadata(
                rule.name,
                "removed_user_mention_names",
                " ".join((f"`{m}`" for m in removed_user_mentions)),
            )

        # Add removed role mentions fields to event
        if removed_role_mentions:
            event.set_metadata(
                rule.name,
                "removed_role_mentions",
                " ".join((m.mention for m in removed_role_mentions)),
            )
            event.set_metadata(
                rule.name,
                "removed_role_mention_names",
                " ".join((f"`{m}`" for m in removed_role_mentions)),
            )

        # If we got this far, we had removed mentions
        return False
