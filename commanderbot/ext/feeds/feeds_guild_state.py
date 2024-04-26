from dataclasses import dataclass
from typing import Optional

from discord import Embed, Interaction, Role
from discord.utils import format_dt

from commanderbot.ext.feeds.feeds_exceptions import ChannelHasNoSubscriptions
from commanderbot.ext.feeds.feeds_options import FeedsOptions
from commanderbot.ext.feeds.feeds_store import FeedsStore
from commanderbot.ext.feeds.providers import FeedType
from commanderbot.lib import MessageableGuildChannel
from commanderbot.lib.cogs import CogGuildState
from commanderbot.lib.dialogs import ConfirmationResult, respond_with_confirmation
from commanderbot.lib.utils import async_expand


@dataclass
class FeedsGuildState(CogGuildState):
    """
    Encapsulates the state and logic of the feeds cog, at the guild level.

    Attributes
    -----------
    store
        The store used to interface with persistent data in a database-agnostic way.
    options
        The config options for this cog.
    """

    store: FeedsStore
    options: FeedsOptions

    async def subscribe_to_feed(
        self,
        interaction: Interaction,
        channel: MessageableGuildChannel,
        feed: FeedType,
        notification_role: Optional[Role],
        auto_pin: Optional[bool],
    ):
        subscription = await self.store.subscribe(
            channel_id=channel.id,
            feed=feed,
            notification_role_id=notification_role.id if notification_role else None,
            auto_pin=bool(auto_pin),
            user_id=interaction.user.id,
        )
        await interaction.response.send_message(
            f"<#{subscription.channel_id}> has subscribed to the feed `{feed.value}`"
        )

    async def modify_subscription(
        self,
        interaction: Interaction,
        channel: MessageableGuildChannel,
        feed: FeedType,
        notification_role: Optional[Role],
        auto_pin: Optional[bool],
    ):
        subscription = await self.store.modify(
            channel_id=channel.id,
            feed=feed,
            notification_role_id=notification_role.id if notification_role else None,
            auto_pin=bool(auto_pin),
        )
        await interaction.response.send_message(
            f"Modified <#{subscription.channel_id}>'s subscription to the feed `{feed.value}`"
        )

    async def unsubscribe_from_feed(
        self, interaction: Interaction, channel: MessageableGuildChannel, feed: FeedType
    ):
        # Try to get the subscription
        subscription = await self.store.require_subscription(channel.id, feed)

        # Respond to this interaction with a confirmation dialog
        result: ConfirmationResult = await respond_with_confirmation(
            interaction,
            f"Are you sure you want to unsubscribe <#{subscription.channel_id}> from the feed `{feed.value}`?",
            timeout=10.0,
        )

        match result:
            case ConfirmationResult.YES:
                # If the answer was yes, try to unsubscribe and send a response
                try:
                    await self.store.unsubscribe(channel.id, feed)
                    await interaction.followup.send(
                        f"<#{subscription.channel_id}> has unsubscribed from the feed `{feed.value}`"
                    )
                except Exception as ex:
                    await interaction.delete_original_response()
                    raise ex
            case _:
                # If the answer was no, send a response
                await interaction.followup.send(
                    f"Did not unsubscribe <#{subscription.channel_id}> from the feed `{feed.value}`"
                )

    async def show_subscription_details(
        self, interaction: Interaction, channel: MessageableGuildChannel
    ):
        subscriptions = await async_expand(self.store.get_subscriptions(channel.id))
        if not subscriptions:
            raise ChannelHasNoSubscriptions(channel.id)

        embed = Embed(title=f"Subscription details for <#{channel.id}>", color=0x00ACED)
        for feed, subscription in subscriptions:
            rows = []

            # Add notification role
            if role_id := subscription.notification_role_id:
                rows.append(f"- **Notification Role**: <@&{role_id}>")

            # Add auto pin
            if subscription.auto_pin:
                current_pin = "**None!**"
                if subscription.current_pin_id:
                    pinned_message = channel.get_partial_message(
                        subscription.current_pin_id
                    )
                    current_pin = pinned_message.jump_url
                rows.append(f"- **Current Pin**: {current_pin}")

            # Add subscriber info
            rows.append(
                f"- **Subscribed By**: <@{subscription.subscriber_id}> ({format_dt(subscription.subscribed_on, 'R')})"
            )

            # Finally, all the field to the embed
            embed.add_field(name=feed.value, value="\n".join(rows), inline=False)

        await interaction.response.send_message(embed=embed)
