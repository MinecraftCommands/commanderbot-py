from discord import (
    ForumChannel,
    Interaction,
    Message,
    PartialEmoji,
    Permissions,
    RawReactionActionEvent,
    RawThreadUpdateEvent,
    Thread,
)
from discord.app_commands import Group, Transform, command, describe, guild_only
from discord.enums import MessageType
from discord.ext.commands import Bot, Cog

from commanderbot.ext.help_forum.help_forum_data import HelpForumData
from commanderbot.ext.help_forum.help_forum_exceptions import (
    InvalidResolveLocation,
    UnableToResolvePinned,
)
from commanderbot.ext.help_forum.help_forum_guild_state import HelpForumGuildState
from commanderbot.ext.help_forum.help_forum_json_store import HelpForumJsonStore
from commanderbot.ext.help_forum.help_forum_options import HelpForumOptions
from commanderbot.ext.help_forum.help_forum_state import HelpForumState
from commanderbot.ext.help_forum.help_forum_store import HelpForumStore
from commanderbot.lib import is_bot, is_forum_channel, is_guild, is_thread
from commanderbot.lib.app_commands import EmojiTransformer
from commanderbot.lib.cogs import CogGuildStateManager
from commanderbot.lib.cogs.database import (
    InMemoryDatabaseOptions,
    JsonFileDatabaseAdapter,
    JsonFileDatabaseOptions,
    UnsupportedDatabaseOptions,
)


def _make_store(bot: Bot, cog: Cog, options: HelpForumOptions) -> HelpForumStore:
    db_options = options.database
    if isinstance(db_options, InMemoryDatabaseOptions):
        return HelpForumData()
    if isinstance(db_options, JsonFileDatabaseOptions):
        return HelpForumJsonStore(
            bot=bot,
            cog=cog,
            db=JsonFileDatabaseAdapter(
                options=db_options,
                serializer=lambda cache: cache.to_json(),
                deserializer=HelpForumData.from_data,
            ),
        )
    raise UnsupportedDatabaseOptions(db_options)


class HelpForumCog(Cog, name="commanderbot.ext.help_forum"):
    def __init__(self, bot: Bot, **options):
        self.bot: Bot = bot
        self.options = HelpForumOptions.from_data(options)
        self.store: HelpForumStore = _make_store(self.bot, self, self.options)
        self.state = HelpForumState(
            bot=self.bot,
            cog=self,
            guilds=CogGuildStateManager(
                bot=self.bot,
                cog=self,
                factory=lambda guild: HelpForumGuildState(
                    bot=self.bot, cog=self, guild=guild, store=self.store
                ),
            ),
            store=self.store,
        )

    # @@ LISTENERS

    @Cog.listener()
    async def on_thread_create(self, thread: Thread):
        # Make sure this thread was created in a forum channel
        forum = thread.parent
        if not is_forum_channel(forum):
            return

        await self.state[forum.guild].on_thread_create(forum, thread)

    @Cog.listener()
    async def on_raw_thread_update(self, payload: RawThreadUpdateEvent):
        # Ignore updates to threads that are in the cache
        if payload.thread:
            return

        # Ignore updates if the ID doesn't refer to a thread for some reason
        thread = await self.bot.fetch_channel(payload.thread_id)
        if not is_thread(thread):
            return

        # Ignored pinned threads
        if thread.flags.pinned:
            return

        # Make sure this thread is in a forum channel
        forum = thread.parent
        if not is_forum_channel(forum):
            return

        await self.state[forum.guild].on_unresolve(forum, thread)

    @Cog.listener()
    async def on_message(self, message: Message):
        # Make sure this message was sent in a thread
        thread = message.channel
        if not is_thread(thread):
            return

        # Ignore pinned threads
        if thread.flags.pinned:
            return

        # Make sure this thread is in a forum channel
        forum = thread.parent
        if not is_forum_channel(forum):
            return

        # Try resolving the thread
        if not is_bot(self.bot, message.author):
            emoji = PartialEmoji.from_str(message.content)
            await self.state[forum.guild].on_resolve(forum, thread, message, emoji)
        # Try deleting the message if it was a pin message sent by the bot
        elif message.type == MessageType.pins_add:
            await self.state[forum.guild].on_bot_pin_starter_message(
                forum, thread, message
            )

    @Cog.listener()
    async def on_raw_reaction_add(self, payload: RawReactionActionEvent):
        # Make sure this reaction was not added by the bot
        if is_bot(self.bot, payload.user_id):
            return

        # Make sure this reaction was added to a message in a thread
        thread = await self.bot.fetch_channel(payload.channel_id)
        if not is_thread(thread):
            return

        # Ignore pinned threads
        if thread.flags.pinned:
            return

        # Make sure this thread is in a forum channel
        forum = thread.parent
        if not is_forum_channel(forum):
            return

        message = thread.get_partial_message(payload.message_id)
        emoji = payload.emoji
        await self.state[forum.guild].on_resolve(forum, thread, message, emoji)

    # @@ COMMANDS

    # Groups
    cmd_forum = Group(
        name="forum",
        description="Manage help forums",
        guild_only=True,
        default_permissions=Permissions(administrator=True),
    )
    cmd_forum_modify = Group(
        name="modify", description="Modify help forums", parent=cmd_forum
    )

    # @@ User facing commands

    @command(name="resolve", description="Resolve a post in a help forum")
    @guild_only()
    async def cmd_resolve(self, interaction: Interaction):
        # Make sure this command was ran from a thread
        thread = interaction.channel
        if not is_thread(thread):
            raise InvalidResolveLocation

        # Make sure this thread is in a forum channel
        forum = thread.parent
        if not is_forum_channel(forum):
            raise InvalidResolveLocation

        # Make sure this thread isn't pinned
        if thread.flags.pinned:
            raise UnableToResolvePinned

        assert is_guild(interaction.guild)
        await interaction.response.defer()
        await self.state[interaction.guild].on_resolve_command(
            interaction, forum, thread
        )

    # @@ forum register/deregister/details

    @cmd_forum.command(
        name="register", description="Register a forum channel as a help forum"
    )
    @describe(
        forum="The forum channel to register",
        resolved_emoji="The emoji that's used for resolving posts",
        unresolved_tag="The tag for unresolved posts",
        resolved_tag="The tag for resolved posts",
    )
    async def cmd_forum_register(
        self,
        interaction: Interaction,
        forum: ForumChannel,
        resolved_emoji: Transform[str, EmojiTransformer],
        unresolved_tag: str,
        resolved_tag: str,
    ):
        assert is_guild(interaction.guild)
        await self.state[interaction.guild].register_forum_channel(
            interaction, forum, resolved_emoji, unresolved_tag, resolved_tag
        )

    @cmd_forum.command(
        name="deregister",
        description="Deregister a forum channel from being a help forum",
    )
    @describe(forum="The help forum to deregister")
    async def cmd_forum_deregister(self, interaction: Interaction, forum: ForumChannel):
        assert is_guild(interaction.guild)
        await self.state[interaction.guild].deregister_forum_channel(interaction, forum)

    @cmd_forum.command(
        name="details", description="Show the details about a help forum"
    )
    @describe(forum="The help forum to show details about")
    async def cmd_forum_details(self, interaction: Interaction, forum: ForumChannel):
        assert is_guild(interaction.guild)
        await self.state[interaction.guild].details(interaction, forum)

    # @@ forum modify

    @cmd_forum_modify.command(
        name="resolved-emoji", description="Modify the resolved emoji for a help forum"
    )
    @describe(forum="The help forum to modify", emoji="The new emoji")
    async def cmd_forum_modify_resolved_emoji(
        self,
        interaction: Interaction,
        forum: ForumChannel,
        emoji: Transform[str, EmojiTransformer],
    ):
        assert is_guild(interaction.guild)
        await self.state[interaction.guild].modify_resolved_emoji(
            interaction, forum, emoji
        )

    @cmd_forum_modify.command(
        name="unresolved-tag", description="Modify the unresolved tag for a help forum"
    )
    @describe(forum="The help forum to modify", tag="ID or name of the new tag")
    async def cmd_forum_modify_unresolved_tag(
        self, interaction: Interaction, forum: ForumChannel, tag: str
    ):
        assert is_guild(interaction.guild)
        await self.state[interaction.guild].modify_unresolved_tag(
            interaction, forum, tag
        )

    @cmd_forum_modify.command(
        name="resolved-tag", description="Modify the resolved tag for a help forum"
    )
    @describe(forum="The help forum to modify", tag="ID or name of the new tag")
    async def cmd_forum_modify_resolved_tag(
        self, interaction: Interaction, forum: ForumChannel, tag: str
    ):
        assert is_guild(interaction.guild)
        await self.state[interaction.guild].modify_resolved_tag(interaction, forum, tag)
