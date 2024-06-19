from enum import Enum
from typing import Optional

from discord import Guild, Interaction, Permissions, Role
from discord.app_commands import Group, describe
from discord.ext.commands import Bot, Cog

from commanderbot.ext.feeds.feeds_data import FeedsData
from commanderbot.ext.feeds.feeds_guild_state import FeedsGuildState
from commanderbot.ext.feeds.feeds_json_store import FeedsJsonStore
from commanderbot.ext.feeds.feeds_options import FeedsOptions
from commanderbot.ext.feeds.feeds_state import FeedsState
from commanderbot.ext.feeds.feeds_store import FeedsStore
from commanderbot.ext.feeds.providers import (
    FeedType,
    FeedProviderType,
    MinecraftBedrockUpdates,
    MinecraftJavaJarUpdates,
    MinecraftJavaUpdates,
)
from commanderbot.lib import MessageableGuildChannel
from commanderbot.lib.cogs import CogGuildStateManager
from commanderbot.lib.cogs.database import (
    InMemoryDatabaseOptions,
    JsonFileDatabaseAdapter,
    JsonFileDatabaseOptions,
    UnsupportedDatabaseOptions,
)
from commanderbot.lib.app_commands import checks


class FeedProviderChoices(Enum):
    minecraft_java_updates = FeedProviderType.MINECRAFT_JAVA_UPDATES
    minecraft_bedrock_updates = FeedProviderType.MINECRAFT_BEDROCK_UPDATES
    minecraft_java_jar_updates = FeedProviderType.MINECRAFT_JAVA_JAR_UPDATES


class FeedChoices(Enum):
    minecraft_java_releases = FeedType.MINECRAFT_JAVA_RELEASES
    minecraft_java_snapshots = FeedType.MINECRAFT_JAVA_SNAPSHOTS
    minecraft_bedrock_releases = FeedType.MINECRAFT_BEDROCK_RELEASES
    minecraft_bedrock_previews = FeedType.MINECRAFT_BEDROCK_PREVIEWS
    minecraft_java_release_jars = FeedType.MINECRAFT_JAVA_RELEASE_JARS
    minecraft_java_snapshot_jars = FeedType.MINECRAFT_JAVA_SNAPSHOT_JARS


def _make_store(bot: Bot, cog: Cog, options: FeedsOptions) -> FeedsStore:
    db_options = options.database
    if isinstance(db_options, InMemoryDatabaseOptions):
        return FeedsData()
    if isinstance(db_options, JsonFileDatabaseOptions):
        return FeedsJsonStore(
            bot=bot,
            cog=cog,
            db=JsonFileDatabaseAdapter(
                options=db_options,
                serializer=lambda cache: cache.to_json(),
                deserializer=FeedsData.from_data,
            ),
        )
    raise UnsupportedDatabaseOptions(db_options)


class FeedsCog(Cog, name="commanderbot.ext.feeds"):
    def __init__(self, bot: Bot, **options):
        self.bot: Bot = bot
        self.options = FeedsOptions.from_data(options)
        self.store: FeedsStore = _make_store(self.bot, self, self.options)
        self.state = FeedsState(
            bot=self.bot,
            cog=self,
            guilds=CogGuildStateManager(
                self.bot,
                self,
                factory=lambda guild: FeedsGuildState(
                    self.bot, self, guild, self.store, self.options
                ),
            ),
            store=self.store,
            options=self.options,
            mcje_updates=MinecraftJavaUpdates.from_options(
                self.options.minecraft_java_updates
            ),
            mcbe_updates=MinecraftBedrockUpdates.from_options(
                self.options.minecraft_bedrock_updates
            ),
            mcje_jar_updates=MinecraftJavaJarUpdates.from_options(
                self.options.minecraft_java_jar_updates
            ),
        )

    async def cog_load(self):
        self.state.mcje_updates.start()
        self.state.mcbe_updates.start()
        self.state.mcje_jar_updates.start()

    async def cog_unload(self):
        self.state.mcje_updates.stop()
        self.state.mcbe_updates.stop()
        self.state.mcje_jar_updates.stop()

    # @@ COMMANDS

    # @@ feed

    cmd_feed = Group(
        name="feed",
        description="Manage feeds",
        guild_only=True,
        default_permissions=Permissions(administrator=True),
    )

    # @@ feed subscribe
    @cmd_feed.command(name="subscribe", description="Subscribe a channel to a feed")
    @describe(
        channel="The channel to subscribe to a feed",
        feed="The feed to subscribe to",
        notification_role="The role to ping when the feed has new content",
        auto_pin="Keep the latest message from this feed pinned",
    )
    async def cmd_feed_subscribe(
        self,
        interaction: Interaction,
        channel: MessageableGuildChannel,
        feed: FeedChoices,
        notification_role: Optional[Role],
        auto_pin: Optional[bool],
    ):
        assert isinstance(interaction.guild, Guild)
        await self.state[interaction.guild].subscribe_to_feed(
            interaction, channel, feed.value, notification_role, auto_pin
        )

    # @@ feed modify
    @cmd_feed.command(name="modify", description="Modify a channel's feed subscription")
    @describe(
        channel="The channel that was subscribed to a feed",
        feed="The feed that was subscribed to",
        notification_role="The role to ping when the feed has new content",
        auto_pin="Keep the latest message from this feed pinned",
    )
    async def cmd_feed_modify(
        self,
        interaction: Interaction,
        channel: MessageableGuildChannel,
        feed: FeedChoices,
        notification_role: Optional[Role],
        auto_pin: Optional[bool],
    ):
        assert isinstance(interaction.guild, Guild)
        await self.state[interaction.guild].modify_subscription(
            interaction, channel, feed.value, notification_role, auto_pin
        )

    # @@ feed unsubscribe
    @cmd_feed.command(
        name="unsubscribe", description="Unsubscribe a channel from a feed"
    )
    @describe(
        channel="The channel to unsubscribe from a feed",
        feed="The feed to unsubscribe from",
    )
    async def cmd_feed_unsubscribe(
        self,
        interaction: Interaction,
        channel: MessageableGuildChannel,
        feed: FeedChoices,
    ):
        assert isinstance(interaction.guild, Guild)
        await self.state[interaction.guild].unsubscribe_from_feed(
            interaction, channel, feed.value
        )

    # @@ feed details
    @cmd_feed.command(
        name="details", description="Show details about a channel's feed subscriptions"
    )
    @describe(channel="The channel to show subscription details about")
    async def cmd_feed_details(
        self, interaction: Interaction, channel: MessageableGuildChannel
    ):
        assert isinstance(interaction.guild, Guild)
        await self.state[interaction.guild].show_subscription_details(
            interaction, channel
        )

    # @@ feeds

    cmd_feeds = Group(
        name="feeds",
        description="Manage feed providers",
        guild_only=True,
        default_permissions=Permissions(administrator=True),
    )

    # @@ feeds status
    @cmd_feeds.command(name="status", description="Shows the status of a feed provider")
    @describe(feed_provider="The feed provider to show the status of")
    @checks.is_owner()
    async def cmd_feeds_status(
        self, interaction: Interaction, feed_provider: FeedProviderChoices
    ):
        await self.state.feed_provider_status(interaction, feed_provider.value)

    # @@ feeds restart
    @cmd_feeds.command(name="restart", description="Restarts a feed provider")
    @describe(feed_provider="The feed provider to restart")
    @checks.is_owner()
    async def cmd_feeds_restart(
        self, interaction: Interaction, feed_provider: FeedProviderChoices
    ):
        await self.state.restart_feed_provider(interaction, feed_provider.value)
