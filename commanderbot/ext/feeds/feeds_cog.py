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
from commanderbot.lib.interactions import checks


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
        )

    async def cog_load(self):
        self.state.mcje_updates.start()
        self.state.mcbe_updates.start()

    async def cog_unload(self):
        self.state.mcje_updates.start()
        self.state.mcbe_updates.start()

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
        feed="The feed to subscribe to",
        channel="The channel that will receive updates from the feed",
        notification_role="The role to ping when the feed has a new update",
    )
    async def cmd_feed_subscribe(
        self,
        interaction: Interaction,
        feed: FeedType,
        channel: MessageableGuildChannel,
        notification_role: Optional[Role],
    ):
        assert isinstance(interaction.guild, Guild)
        await self.state[interaction.guild].subscribe_to_feed(
            interaction, feed, channel, notification_role
        )

    # @@ feed modify
    @cmd_feed.command(name="modify", description="Modify a channel's feed subscription")
    @describe(
        feed="The feed that was subscribed to",
        channel="The channel that was subscribed to the feed",
        notification_role="The role to ping when the feed has a new update",
    )
    async def cmd_feed_modify(
        self,
        interaction: Interaction,
        feed: FeedType,
        channel: MessageableGuildChannel,
        notification_role: Optional[Role],
    ):
        assert isinstance(interaction.guild, Guild)
        await self.state[interaction.guild].modify_subscription(
            interaction, feed, channel, notification_role
        )

    # @@ feed unsubscribe
    @cmd_feed.command(
        name="unsubscribe", description="Unsubscribe a channel from a feed"
    )
    @describe(
        feed="The feed to unsubscribe from",
        channel="The channel to unsubscribe from the feed",
    )
    async def cmd_feed_unsubscribe(
        self, interaction: Interaction, feed: FeedType, channel: MessageableGuildChannel
    ):
        assert isinstance(interaction.guild, Guild)
        await self.state[interaction.guild].unsubscribe_from_feed(
            interaction, feed, channel
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
        default_permissions=Permissions(administrator=True),
    )

    # @@ feeds status
    @cmd_feeds.command(name="status", description="Shows the status of a feed provider")
    @describe(feed_provider="The feed provider to show the status of")
    @checks.is_owner()
    async def cmd_feeds_status(
        self, interaction: Interaction, feed_provider: FeedProviderType
    ):
        await self.state.feed_provider_status(interaction, feed_provider)

    # @@ feeds restart
    @cmd_feeds.command(name="restart", description="Restarts a feed provider")
    @describe(feed_provider="The feed provider to restart")
    @checks.is_owner()
    async def cmd_feeds_restart(
        self, interaction: Interaction, feed_provider: FeedProviderType
    ):
        await self.state.restart_feed_provider(interaction, feed_provider)
