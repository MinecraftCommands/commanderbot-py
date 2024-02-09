from dataclasses import dataclass

from discord import Embed, Interaction
from discord.utils import format_dt

from commanderbot.ext.feeds.feeds_guild_state import FeedsGuildState
from commanderbot.ext.feeds.feeds_options import FeedsOptions
from commanderbot.ext.feeds.feeds_store import FeedsStore
from commanderbot.ext.feeds.providers import (
    FeedProvider,
    FeedProviderOptions,
    FeedProviderType,
    MinecraftBedrockUpdates,
    MinecraftJavaUpdates,
    MinecraftUpdateInfo,
)
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

    async def _on_mcje_release(self, update_info: MinecraftUpdateInfo):
        # Get the feed provider options
        options = self.options.minecraft_java_updates

    async def _on_mcje_snapshot(self, update_info: MinecraftUpdateInfo):
        # Get the feed provider options
        options = self.options.minecraft_java_updates

    async def _on_mcbe_release(self, update_info: MinecraftUpdateInfo):
        # Get the feed provider options
        options = self.options.minecraft_bedrock_updates

    async def _on_mcbe_preview(self, update_info: MinecraftUpdateInfo):
        # Get the feed provider options
        options = self.options.minecraft_bedrock_updates

    def _get_provider(self, feed_provider: FeedProviderType) -> FeedProvider:
        """
        Returns a `Protocol` that only contains attributes that are common
        between feed providers
        """
        match feed_provider:
            case FeedProviderType.minecraft_java_updates:
                return self.mcje_updates
            case FeedProviderType.minecraft_bedrock_updates:
                return self.mcbe_updates
            case _:
                raise KeyError

    def _get_options(self, feed_provider: FeedProviderType) -> FeedProviderOptions:
        """
        Returns a `Protocol` that only contains attributes that are common
        between feed provider options
        """
        match feed_provider:
            case FeedProviderType.minecraft_java_updates:
                return self.options.minecraft_java_updates
            case FeedProviderType.minecraft_bedrock_updates:
                return self.options.minecraft_bedrock_updates
            case _:
                raise KeyError

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
