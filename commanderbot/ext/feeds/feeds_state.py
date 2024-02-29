from dataclasses import dataclass

from discord import Embed, Interaction, ui
from discord.utils import format_dt

from commanderbot.ext.feeds.feeds_guild_state import FeedsGuildState
from commanderbot.ext.feeds.feeds_options import FeedsOptions
from commanderbot.ext.feeds.feeds_store import FeedsStore
from commanderbot.ext.feeds.providers import (
    FeedProvider,
    FeedProviderOptions,
    FeedProviderType,
    FeedType,
    MinecraftBedrockUpdates,
    MinecraftJavaUpdates,
    MinecraftUpdateInfo,
)
from commanderbot.lib import ChannelID, Color, MessageableGuildChannel
from commanderbot.lib.cogs import GuildPartitionedCogState


@dataclass
class FeedsState(GuildPartitionedCogState[FeedsGuildState]):
    """
    Encapsulates the state and logic of the feeds cog, for each guild.

    Attributes
    -----------
    store
        The store used to interface with persistent data in a database-agnostic way.
    options
        The config options for this cog.
    mcje_updates
        Feed provider for Minecraft Java updates.
    mcbe_updates
        Feed provider for Minecraft Bedrock updates.
    """

    store: FeedsStore
    options: FeedsOptions
    mcje_updates: MinecraftJavaUpdates
    mcbe_updates: MinecraftBedrockUpdates

    def __post_init__(self):
        # Setup feed handlers
        self.mcje_updates.release_handler = self._on_mcje_release
        self.mcje_updates.snapshot_handler = self._on_mcje_snapshot
        self.mcbe_updates.release_handler = self._on_mcbe_release
        self.mcbe_updates.preview_handler = self._on_mcbe_preview

    async def _get_channel(self, channel_id: ChannelID) -> MessageableGuildChannel:
        channel = self.bot.get_channel(channel_id)
        if not channel:
            channel = await self.bot.fetch_channel(channel_id)
        assert isinstance(channel, MessageableGuildChannel)
        return channel

    def _get_provider(self, feed_provider: FeedProviderType) -> FeedProvider:
        """
        Returns a `Protocol` that only contains attributes that are common
        between feed providers
        """
        match feed_provider:
            case FeedProviderType.MINECRAFT_JAVA_UPDATES:
                return self.mcje_updates
            case FeedProviderType.MINECRAFT_BEDROCK_UPDATES:
                return self.mcbe_updates
            case _:
                raise KeyError

    def _get_options(self, feed_provider: FeedProviderType) -> FeedProviderOptions:
        """
        Returns a `Protocol` that only contains attributes that are common
        between feed provider options
        """
        match feed_provider:
            case FeedProviderType.MINECRAFT_JAVA_UPDATES:
                return self.options.minecraft_java_updates
            case FeedProviderType.MINECRAFT_BEDROCK_UPDATES:
                return self.options.minecraft_bedrock_updates
            case _:
                raise KeyError

    def _create_mc_update_buttons(self, update_info: MinecraftUpdateInfo) -> ui.View:
        view = ui.View()
        view.add_item(ui.Button(label="Changelog", url=update_info.url))
        view.add_item(ui.Button(label="Jira", url="https://bugs.mojang.com/"))
        view.add_item(
            ui.Button(label="Feedback", url="https://feedback.minecraft.net/")
        )
        return view

    async def _send_mc_update_to_subscribers(
        self,
        feed: FeedType,
        update_info: MinecraftUpdateInfo,
        update_embed: Embed,
        update_buttons: ui.View,
    ):
        async for subscriber in self.store.subscribers(feed):
            try:
                # Get the channel and the send the update
                channel = await self._get_channel(subscriber.channel_id)
                msg = await channel.send(embed=update_embed, view=update_buttons)

                # Ping the notification role if it's configured
                if subscriber.notification_role_id:
                    await msg.reply(
                        f"<@&{subscriber.notification_role_id}> {update_info.version} has been released!",
                        mention_author=False,
                    )
            except:
                pass

    async def _on_mcje_release(self, update_info: MinecraftUpdateInfo):
        """
        Handler for Minecraft: Java Edition Releases
        """
        # Get feed type and options
        feed = FeedType.MINECRAFT_JAVA_RELEASES
        options = self.options.minecraft_java_updates

        # Create embed
        update_embed = Embed(
            title=update_info.title,
            url=update_info.url,
            color=Color.minecraft_green(),
            timestamp=update_info.published,
        )
        update_embed.set_author(name=feed.value, icon_url=options.feed_icon_url)
        update_embed.set_thumbnail(url=options.release_icon_url)
        update_embed.set_image(url=update_info.thumbnail_url)

        # Create buttons
        update_buttons = self._create_mc_update_buttons(update_info)

        # Send update embed to subscribers
        await self._send_mc_update_to_subscribers(
            feed, update_info, update_embed, update_buttons
        )

    async def _on_mcje_snapshot(self, update_info: MinecraftUpdateInfo):
        """
        Handler for Minecraft: Java Edition Snapshots
        """
        # Get feed type and options
        feed = FeedType.MINECRAFT_JAVA_SNAPSHOTS
        options = self.options.minecraft_java_updates

        # Create embed and buttons
        update_embed = Embed(
            title=update_info.title,
            url=update_info.url,
            color=Color.minecraft_gold(),
            timestamp=update_info.published,
        )
        update_embed.set_author(name=feed.value, icon_url=options.feed_icon_url)
        update_embed.set_thumbnail(url=options.snapshot_icon_url)
        update_embed.set_image(url=update_info.thumbnail_url)

        # Create buttons
        update_buttons = self._create_mc_update_buttons(update_info)

        # Send update embed to subscribers
        await self._send_mc_update_to_subscribers(
            feed, update_info, update_embed, update_buttons
        )

    async def _on_mcbe_release(self, update_info: MinecraftUpdateInfo):
        """
        Handler for Minecraft: Bedrock Edition Releases
        """
        # Get feed type and options
        feed = FeedType.MINECRAFT_BEDROCK_RELEASES
        options = self.options.minecraft_bedrock_updates

        # Create embed
        update_embed = Embed(
            title=update_info.title,
            url=update_info.url,
            color=Color.minecraft_material_emerald(),
            timestamp=update_info.published,
        )
        update_embed.set_author(name=feed.value, icon_url=options.feed_icon_url)
        update_embed.set_thumbnail(url=options.release_icon_url)
        update_embed.set_image(url=update_info.thumbnail_url)

        # Create buttons
        update_buttons = self._create_mc_update_buttons(update_info)

        # Send update embed to subscribers
        await self._send_mc_update_to_subscribers(
            feed, update_info, update_embed, update_buttons
        )

    async def _on_mcbe_preview(self, update_info: MinecraftUpdateInfo):
        """
        Handler for Minecraft: Bedrock Edition Snapshots
        """
        # Get feed type and options
        feed = FeedType.MINECRAFT_BEDROCK_PREVIEWS
        options = self.options.minecraft_bedrock_updates

        # Create embed
        update_embed = Embed(
            title=update_info.title,
            url=update_info.url,
            color=Color.minecraft_material_gold(),
            timestamp=update_info.published,
        )
        update_embed.set_author(name=feed.value, icon_url=options.feed_icon_url)
        update_embed.set_thumbnail(url=options.preview_icon_url)
        update_embed.set_image(url=update_info.thumbnail_url)

        # Create buttons
        update_buttons = self._create_mc_update_buttons(update_info)

        # Send update embed to subscribers
        await self._send_mc_update_to_subscribers(
            feed, update_info, update_embed, update_buttons
        )

    async def feed_provider_status(
        self, interaction: Interaction, feed_provider: FeedProviderType
    ):
        # Get the feed provider and options
        provider = self._get_provider(feed_provider)
        options = self._get_options(feed_provider)

        # Format data from the feed provider
        formatted_prev_update = "**?**"
        if dt := provider.prev_request_date:
            formatted_prev_update = format_dt(dt, "R")

        formatted_next_update = "**?**"
        if dt := provider.next_request_date:
            formatted_next_update = format_dt(dt, "R")

        formatted_prev_status_code = f"`{provider.prev_status_code}`" or "**?**"

        # Create feed provider status embed
        embed = Embed(title=feed_provider.value, color=0x00ACED)
        embed.add_field(name="URL", value=provider.url, inline=False)
        embed.add_field(name="Previous Update", value=formatted_prev_update)
        embed.add_field(name="Next Update", value=formatted_next_update)
        embed.add_field(name="Previous Status Code", value=formatted_prev_status_code)
        embed.set_thumbnail(url=options.feed_icon_url)

        await interaction.response.send_message(embed=embed)

    async def restart_feed_provider(
        self, interaction: Interaction, feed_provider: FeedProviderType
    ):
        provider = self._get_provider(feed_provider)
        provider.restart()
        await interaction.response.send_message(
            f"✅ Restarted feed provider `{feed_provider.value}`"
        )
