from discord import ForumChannel, Interaction, Message, Permissions
from discord.app_commands import (
    AppCommandContext,
    AppInstallationType,
    Choice,
    Group,
    autocomplete,
    describe,
)
from discord.ext.commands import Bot, Cog

from commanderbot.ext.friday.friday_data import FridayData
from commanderbot.ext.friday.friday_guild_state import FridayGuildState
from commanderbot.ext.friday.friday_json_store import FridayJsonStore
from commanderbot.ext.friday.friday_options import FridayOptions
from commanderbot.ext.friday.friday_state import FridayState
from commanderbot.ext.friday.friday_store import FridayStore
from commanderbot.lib import (
    MessageableGuildChannel,
    constants,
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

    # @@ AUTOCOMPLETE

    async def rule_autocomplete(
        self, interaction: Interaction, value: str
    ) -> list[Choice[str]]:
        """
        An autocomplete callback that will return any rules that match `value`
        """

        choices: list[Choice] = []
        assert is_guild(interaction.guild)
        async for rule in self.store.get_rules(
            interaction.guild,
            rule_filter=value,
            sort=True,
            cap=constants.MAX_AUTOCOMPLETE_CHOICES,
        ):
            choices.append(Choice(name=f"📜 {rule.name}", value=rule.name))
        return choices

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

    # @@ friday channels
    cmd_friday_channels = Group(
        name="channels", description="Manage channels", parent=cmd_friday
    )

    # @@ friday channels register
    @cmd_friday_channels.command(
        name="register", description="Register a channel so rules will be checked in it"
    )
    @describe(channel="The channel to register")
    async def cmd_friday_channels_register(
        self, interaction: Interaction, channel: MessageableGuildChannel | ForumChannel
    ):
        assert is_guild(interaction.guild)
        await self.state[interaction.guild].register_channel(interaction, channel.id)

    # @@ friday channels unregister
    @cmd_friday_channels.command(
        name="unregister",
        description="Unregister a channel so rules will not be checked in it",
    )
    @describe(channel="The channel to unregister")
    async def cmd_friday_channels_unregister(
        self, interaction: Interaction, channel: MessageableGuildChannel | ForumChannel
    ):
        assert is_guild(interaction.guild)
        await self.state[interaction.guild].unregister_channel(interaction, channel.id)

    # @@ friday channels list
    @cmd_friday_channels.command(
        name="list",
        description="List all registered channels",
    )
    async def cmd_friday_channels_list(self, interaction: Interaction):
        assert is_guild(interaction.guild)
        await self.state[interaction.guild].list_registered_channels(interaction)

    # @@ friday rules
    cmd_friday_rules = Group(
        name="rules", description="Manage rules", parent=cmd_friday
    )

    # @@ friday rules add
    @cmd_friday_rules.command(name="add", description="Add a new rule")
    async def cmd_friday_rules_add(self, interaction: Interaction):
        assert is_guild(interaction.guild)
        await self.state[interaction.guild].add_rule(interaction)

    # @@ friday rules modify
    @cmd_friday_rules.command(name="modify", description="Modify a rule")
    @autocomplete(rule=rule_autocomplete)
    async def cmd_friday_rules_modify(self, interaction: Interaction, rule: str):
        assert is_guild(interaction.guild)
        await self.state[interaction.guild].modify_rule(interaction, rule)

    # @@ friday rules remove
    @cmd_friday_rules.command(name="remove", description="Remove a rule")
    @autocomplete(rule=rule_autocomplete)
    async def cmd_friday_rules_remove(self, interaction: Interaction, rule: str):
        assert is_guild(interaction.guild)
        await self.state[interaction.guild].remove_rule(interaction, rule)

    # @@ friday rules details
    @cmd_friday_rules.command(
        name="details", description="Show the details about a rule"
    )
    @autocomplete(rule=rule_autocomplete)
    async def cmd_friday_rules_details(self, interaction: Interaction, rule: str):
        assert is_guild(interaction.guild)
        await self.state[interaction.guild].show_rule_details(interaction, rule)

    # @@ friday rules list
    @cmd_friday_rules.command(name="list", description="List all rules")
    async def cmd_friday_rules_list(self, interaction: Interaction):
        assert is_guild(interaction.guild)
        await self.state[interaction.guild].list_rules(interaction)
