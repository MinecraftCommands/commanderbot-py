from discord import ForumChannel, Interaction, Message, Permissions
from discord.app_commands import AppCommandContext, AppInstallationType, Group, describe
from discord.ext.commands import Bot, Cog

from commanderbot.ext.friday.friday_data import FridayData
from commanderbot.ext.friday.friday_guild_state import FridayGuildState
from commanderbot.ext.friday.friday_json_store import FridayJsonStore
from commanderbot.ext.friday.friday_options import FridayOptions
from commanderbot.ext.friday.friday_state import FridayState
from commanderbot.ext.friday.friday_store import FridayStore
from commanderbot.lib import (
    MessageableGuildChannel,
    is_bot,
    is_guild,
    is_messagable_guild_channel,
)
from commanderbot.lib.cogs import CogGuildStateManager
from commanderbot.lib.cogs.database import (
    InMemoryDatabaseOptions,
    JsonFileDatabaseAdapter,
    JsonFileDatabaseOptions,
    UnsupportedDatabaseOptions,
)


def _make_store(bot: Bot, cog: Cog, options: FridayOptions) -> FridayStore:
    db_options = options.database
    if isinstance(db_options, InMemoryDatabaseOptions):
        return FridayData()
    elif isinstance(db_options, JsonFileDatabaseOptions):
        return FridayJsonStore(
            bot=bot,
            cog=cog,
            db=JsonFileDatabaseAdapter(
                options=db_options,
                serializer=lambda cache: cache.to_json(),
                deserializer=FridayData.from_data,
            ),
        )
    raise UnsupportedDatabaseOptions(db_options)


class FridayCog(Cog, name="commanderbot.ext.friday"):
    def __init__(self, bot: Bot, **options):
        self.bot: Bot = bot
        self.options = FridayOptions.from_data(options)
        self.store: FridayStore = _make_store(self.bot, self, self.options)
        self.state = FridayState(
            bot=self.bot,
            cog=self,
            guilds=CogGuildStateManager(
                bot=self.bot,
                cog=self,
                factory=lambda guild: FridayGuildState(
                    bot=self.bot, cog=self, guild=guild, store=self.store
                ),
            ),
            store=self.store,
        )

    # @@ LISTENERS

    @Cog.listener()
    async def on_message(self, message: Message):
        # Make sure the message wasn't sent by the bot
        if is_bot(self.bot, message.author):
            return

        # Make sure the message was sent in a messageable channel in a guild
        if not (message.guild and is_messagable_guild_channel(message.channel)):
            return

        await self.state[message.guild].on_message(message)

    # @@ COMMANDS

    # @@ friday

    cmd_friday = Group(
        name="friday",
        description="Today is friday in California",
        allowed_installs=AppInstallationType(guild=True),
        allowed_contexts=AppCommandContext(guild=True),
        default_permissions=Permissions(administrator=True),
    )

    # @@ friday register
    @cmd_friday.command(
        name="register", description="Register a channel so rules will be checked in it"
    )
    @describe(channel="The channel to register")
    async def cmd_register(
        self, interaction: Interaction, channel: MessageableGuildChannel | ForumChannel
    ):
        assert is_guild(interaction.guild)
        await self.state[interaction.guild].register_channel(interaction, channel.id)

    # @@ friday unregister
    @cmd_friday.command(
        name="unregister",
        description="Unregister a channel so rules will not be checked in it",
    )
    @describe(channel="The channel to unregister")
    async def cmd_unregister(
        self, interaction: Interaction, channel: MessageableGuildChannel | ForumChannel
    ):
        assert is_guild(interaction.guild)
        await self.state[interaction.guild].unregister_channel(interaction, channel.id)

    # @@ friday rule
    cmd_friday_rule = Group(name="rule", description="Manage rules", parent=cmd_friday)

    # @@ friday rule add
    @cmd_friday_rule.command(name="add", description="Add a new rule")
    async def cmd_friday_rule_add(self, interaction: Interaction):
        assert is_guild(interaction.guild)
        await self.state[interaction.guild].add_rule(interaction)

    # @@ friday rule modify
    @cmd_friday_rule.command(name="modify", description="Modify a rule")
    async def cmd_friday_rule_modify(self, interaction: Interaction, rule: str):
        assert is_guild(interaction.guild)
        await self.state[interaction.guild].modify_rule(interaction, rule)

    # @@ friday rule remove
    @cmd_friday_rule.command(name="remove", description="Remove a rule")
    async def cmd_friday_rule_remove(self, interaction: Interaction, rule: str):
        assert is_guild(interaction.guild)
        await self.state[interaction.guild].remove_rule(interaction, rule)

    # @@ friday rule details
    @cmd_friday_rule.command(
        name="details", description="Show the details about a rule"
    )
    async def cmd_friday_rule_details(self, interaction: Interaction, rule: str):
        assert is_guild(interaction.guild)
        await self.state[interaction.guild].show_rule_details(interaction, rule)

    # @@ friday rule list
    @cmd_friday_rule.command(name="list", description="List all rules")
    async def cmd_friday_rule_list(self, interaction: Interaction):
        assert is_guild(interaction.guild)
        await self.state[interaction.guild].list_rules(interaction)
