from dataclasses import dataclass
from typing import Optional

from discord import Embed, Interaction, ui
from discord.utils import format_dt

from commanderbot.ext.feeds.feeds_guild_state import FeedsGuildState
from commanderbot.ext.feeds.feeds_options import FeedsOptions
from commanderbot.ext.feeds.feeds_store import FeedsStore
from commanderbot.ext.feeds.providers import (
    FeedProviderBase,
    FeedProviderOptionsBase,
    FeedProviderType,
    FeedType,
    MinecraftBedrockUpdateInfo,
    MinecraftBedrockUpdates,
    MinecraftJavaJarUpdateInfo,
    MinecraftJavaJarUpdates,
    MinecraftJavaUpdateInfo,
    MinecraftJavaUpdates,
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
    mcje_jar_updates: MinecraftJavaJarUpdates

    def __post_init__(self):
        # Setup feed handlers
        self.mcje_updates.release_handler = self._on_mcje_release
        self.mcje_updates.snapshot_handler = self._on_mcje_snapshot
        self.mcbe_updates.release_handler = self._on_mcbe_release
        self.mcbe_updates.preview_handler = self._on_mcbe_preview
        self.mcje_jar_updates.release_handler = self._on_mcje_release_jar
        self.mcje_jar_updates.snapshot_handler = self._on_mcje_snapshot_jar

    # @@ UTILITIES

    def _get_provider(self, feed_provider: FeedProviderType) -> FeedProviderBase:
        match feed_provider:
            case FeedProviderType.MINECRAFT_JAVA_UPDATES:
                return self.mcje_updates
            case FeedProviderType.MINECRAFT_BEDROCK_UPDATES:
                return self.mcbe_updates
            case FeedProviderType.MINECRAFT_JAVA_JAR_UPDATES:
                return self.mcje_jar_updates
            case _:
                raise KeyError

    def _get_options(self, feed_provider: FeedProviderType) -> FeedProviderOptionsBase:
        match feed_provider:
            case FeedProviderType.MINECRAFT_JAVA_UPDATES:
                return self.options.minecraft_java_updates
            case FeedProviderType.MINECRAFT_BEDROCK_UPDATES:
                return self.options.minecraft_bedrock_updates
            case FeedProviderType.MINECRAFT_JAVA_JAR_UPDATES:
                return self.options.minecraft_java_jar_updates
            case _:
                raise KeyError

    async def _send_to_subscribers(
        self,
        feed: FeedType,
        embed: Embed,
        view: Optional[ui.View] = None,
        notification_message: Optional[str] = None,
    ):
        async for subscriber in self.store.subscribers(feed):
            # Format the notification message
            content: Optional[str] = None
            if notification_message and subscriber.notification_role_id:
                role_mention = f"<@&{subscriber.notification_role_id}>"
                content = f"{role_mention} {notification_message}"

            # Get the channel
            channel = self.bot.get_partial_messageable(subscriber.channel_id)

            # Send the embed
            try:
                await channel.send(content=content, embed=embed, view=view)  # type: ignore
            except:
                pass

    def _create_mcje_update_buttons(
        self, update_info: MinecraftJavaUpdateInfo
    ) -> ui.View:
        view = ui.View()
        view.add_item(ui.Button(label="Changelog", url=update_info.url))
        if update_info.mirror_url:
            view.add_item(
                ui.Button(label="Changelog (Mirror)", url=update_info.mirror_url)
            )
        return view

    def _create_mcbe_update_buttons(
        self, update_info: MinecraftBedrockUpdateInfo
    ) -> ui.View:
        view = ui.View()
        view.add_item(ui.Button(label="Changelog", url=update_info.url))
        return view

    def _create_mcje_jar_update_buttons(
        self, update_info: MinecraftJavaJarUpdateInfo
    ) -> ui.View:
        view = ui.View()
        view.add_item(ui.Button(label="Client Jar", url=update_info.client_jar_url))
        view.add_item(ui.Button(label="Server Jar", url=update_info.server_jar_url))
        return view

    # @@ FEEDS

    # @@ Minecraft: Java Edition Releases
    async def _on_mcje_release(self, update_info: MinecraftJavaUpdateInfo):
        embed = Embed(
            title=update_info.title,
            url=update_info.url,
            color=Color.minecraft_green(),
            timestamp=update_info.published,
        )
        embed.set_author(
            name=FeedType.MINECRAFT_JAVA_RELEASES.value,
            icon_url=self.options.minecraft_java_updates.icon_url,
        )
        embed.set_thumbnail(url=self.options.minecraft_java_updates.release_icon_url)
        embed.set_image(url=update_info.thumbnail_url)

        # Send update to subscribers
        await self._send_to_subscribers(
            FeedType.MINECRAFT_JAVA_RELEASES,
            embed,
            self._create_mcje_update_buttons(update_info),
            f"Minecraft: Java Edition {update_info.version} has been released! 🎉",
        )

    # @@ Minecraft: Java Edition Snapshots
    async def _on_mcje_snapshot(self, update_info: MinecraftJavaUpdateInfo):
        embed = Embed(
            title=update_info.title,
            url=update_info.url,
            color=Color.minecraft_gold(),
            timestamp=update_info.published,
        )
        embed.set_author(
            name=FeedType.MINECRAFT_JAVA_SNAPSHOTS.value,
            icon_url=self.options.minecraft_java_updates.icon_url,
        )
        embed.set_thumbnail(url=self.options.minecraft_java_updates.snapshot_icon_url)
        embed.set_image(url=update_info.thumbnail_url)

        # Send update to subscribers
        await self._send_to_subscribers(
            FeedType.MINECRAFT_JAVA_SNAPSHOTS,
            embed,
            self._create_mcje_update_buttons(update_info),
            f"Minecraft: Java Edition {update_info.version} has been released! 📸",
        )

    # @@ Minecraft: Bedrock Edition Releases
    async def _on_mcbe_release(self, update_info: MinecraftBedrockUpdateInfo):
        embed = Embed(
            title=update_info.title,
            url=update_info.url,
            color=Color.minecraft_material_emerald(),
            timestamp=update_info.published,
        )
        embed.set_author(
            name=FeedType.MINECRAFT_BEDROCK_RELEASES.value,
            icon_url=self.options.minecraft_bedrock_updates.icon_url,
        )
        embed.set_thumbnail(url=self.options.minecraft_bedrock_updates.release_icon_url)
        embed.set_image(url=update_info.thumbnail_url)

        # Send update to subscribers
        await self._send_to_subscribers(
            FeedType.MINECRAFT_BEDROCK_RELEASES,
            embed,
            self._create_mcbe_update_buttons(update_info),
            f"Minecraft: Bedrock Edition {update_info.version} has been released! 🍊",
        )

    # @@ Minecraft: Bedrock Edition Previews
    async def _on_mcbe_preview(self, update_info: MinecraftBedrockUpdateInfo):
        embed = Embed(
            title=update_info.title,
            url=update_info.url,
            color=Color.minecraft_material_gold(),
            timestamp=update_info.published,
        )
        embed.set_author(
            name=FeedType.MINECRAFT_BEDROCK_PREVIEWS.value,
            icon_url=self.options.minecraft_bedrock_updates.icon_url,
        )
        embed.set_thumbnail(url=self.options.minecraft_bedrock_updates.preview_icon_url)
        embed.set_image(url=update_info.thumbnail_url)

        # Send update to subscribers
        await self._send_to_subscribers(
            FeedType.MINECRAFT_BEDROCK_PREVIEWS,
            embed,
            self._create_mcbe_update_buttons(update_info),
            f"Minecraft: Bedrock Edition {update_info.version} has been released! 🍌",
        )

    # @@ Minecraft: Java Edition Release Jars
    async def _on_mcje_release_jar(self, jar_update_info: MinecraftJavaJarUpdateInfo):
        embed = Embed(
            title=f"Minecraft: Java Edition {jar_update_info.version}",
            url=jar_update_info.url,
            color=Color.minecraft_material_netherite(),
        )
        embed.set_author(
            name=FeedType.MINECRAFT_JAVA_RELEASE_JARS.value,
            icon_url=self.options.minecraft_java_jar_updates.icon_url,
        )
        embed.set_thumbnail(
            url=self.options.minecraft_java_jar_updates.release_jar_icon_url
        )

        embed.add_field(name="Java Version", value=f"`{jar_update_info.java_version}`")
        embed.add_field(
            name="Client Mappings",
            value=f"[Link]({jar_update_info.client_mappings_url})",
        )
        embed.add_field(
            name="Server Mappings",
            value=f"[Link]({jar_update_info.server_mappings_url})",
        )

        # Send update to subscribers
        await self._send_to_subscribers(
            FeedType.MINECRAFT_JAVA_RELEASE_JARS,
            embed,
            self._create_mcje_jar_update_buttons(jar_update_info),
            f"A jar has been released for Minecraft: Java Edition {jar_update_info.version}! 🎉",
        )

    # @@ Minecraft: Java Edition Snapshot Jars
    async def _on_mcje_snapshot_jar(self, jar_update_info: MinecraftJavaJarUpdateInfo):
        embed = Embed(
            title=f"Minecraft: Java Edition {jar_update_info.version}",
            url=jar_update_info.url,
            color=Color.minecraft_material_copper(),
        )
        embed.set_author(
            name=FeedType.MINECRAFT_JAVA_SNAPSHOT_JARS.value,
            icon_url=self.options.minecraft_java_jar_updates.icon_url,
        )
        embed.set_thumbnail(
            url=self.options.minecraft_java_jar_updates.snapshot_jar_icon_url
        )

        embed.add_field(name="Java Version", value=f"`{jar_update_info.java_version}`")
        embed.add_field(
            name="Client Mappings",
            value=f"[Link]({jar_update_info.client_mappings_url})",
        )
        embed.add_field(
            name="Server Mappings",
            value=f"[Link]({jar_update_info.server_mappings_url})",
        )

        # Send update to subscribers
        await self._send_to_subscribers(
            FeedType.MINECRAFT_JAVA_SNAPSHOT_JARS,
            embed,
            self._create_mcje_jar_update_buttons(jar_update_info),
            f"A jar has been released for Minecraft: Java Edition {jar_update_info.version}! 📸",
        )

    # @@ COMMANDS

    async def feed_provider_status(
        self, interaction: Interaction, feed_provider: FeedProviderType
    ):
        # Get the feed provider
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
        embed.add_field(
            name="Cached Items",
            value=f"`{provider.cached_items}`",
        )
        embed.set_thumbnail(url=options.icon_url)

        await interaction.response.send_message(embed=embed)

    async def restart_feed_provider(
        self, interaction: Interaction, feed_provider: FeedProviderType
    ):
        provider = self._get_provider(feed_provider)
        provider.restart()
        await interaction.response.send_message(
            f"✅ Restarted feed provider `{feed_provider.value}`"
        )
