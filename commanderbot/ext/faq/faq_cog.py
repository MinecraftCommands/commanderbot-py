from typing import Union

from discord import Guild, Interaction, Message, Permissions
from discord.abc import Messageable
from discord.app_commands import Choice, Group, autocomplete, describe
from discord.ext.commands import Bot, Cog

from commanderbot.ext.faq.faq_data import FaqData
from commanderbot.ext.faq.faq_guild_state import FaqGuildState
from commanderbot.ext.faq.faq_json_store import FaqJsonStore
from commanderbot.ext.faq.faq_options import FaqOptions
from commanderbot.ext.faq.faq_state import FaqState
from commanderbot.ext.faq.faq_store import FaqEntry, FaqStore
from commanderbot.lib import MAX_AUTOCOMPLETE_CHOICES
from commanderbot.lib.cogs import CogGuildStateManager
from commanderbot.lib.cogs.database import (
    InMemoryDatabaseOptions,
    JsonFileDatabaseAdapter,
    JsonFileDatabaseOptions,
    UnsupportedDatabaseOptions,
)
from commanderbot.lib.utils import async_expand, is_bot


def _make_store(bot: Bot, cog: Cog, options: FaqOptions) -> FaqStore:
    db_options = options.database
    if isinstance(db_options, InMemoryDatabaseOptions):
        return FaqData()
    elif isinstance(db_options, JsonFileDatabaseOptions):
        return FaqJsonStore(
            bot=bot,
            cog=cog,
            db=JsonFileDatabaseAdapter(
                options=db_options,
                serializer=lambda cache: cache.to_json(),
                deserializer=FaqData.from_data,
            ),
        )
    raise UnsupportedDatabaseOptions(db_options)


class FaqCog(Cog, name="commanderbot.ext.faq"):
    def __init__(self, bot: Bot, **options):
        self.bot: Bot = bot
        self.options = FaqOptions.from_data(options)
        self.store: FaqStore = _make_store(self.bot, self, self.options)
        self.state = FaqState(
            bot=self.bot,
            cog=self,
            guilds=CogGuildStateManager(
                bot=self.bot,
                cog=self,
                factory=lambda guild: FaqGuildState(
                    bot=self.bot,
                    cog=self,
                    guild=guild,
                    store=self.store,
                    options=self.options,
                ),
            ),
            store=self.store,
        )

    # @@ AUTOCOMPLETE
    async def faq_autocomplete(
        self, interaction: Interaction, value: str
    ) -> list[Choice[str]]:
        """
        An autocomplete callback that will return any faqs that match `value`
        """

        # Get all faqs filtered by `value`
        assert isinstance(interaction.guild, Guild)
        entries: list[FaqEntry] = await async_expand(
            self.store.get_faqs(
                interaction.guild,
                faq_filter=value,
                sort=True,
                cap=MAX_AUTOCOMPLETE_CHOICES,
            )
        )

        # Create a list of autocomplete choices and return them
        choices: list[Choice] = []
        for entry in entries:
            choices.append(Choice(name=f"💬 {entry.key}", value=entry.key))
        return choices

    async def faq_and_alias_autocomplete(
        self, interaction: Interaction, value: str
    ) -> list[Choice[str]]:
        """
        An autocomplete callback that will return any faqs or aliases that match `value`
        """

        # Get all faqs and aliases filtered by `value`
        assert isinstance(interaction.guild, Guild)
        items: list[Union[FaqEntry, tuple[str, FaqEntry]]] = await async_expand(
            self.store.get_faqs_and_aliases(
                interaction.guild,
                item_filter=value,
                sort=True,
                cap=MAX_AUTOCOMPLETE_CHOICES,
            )
        )

        # Create a list of autocomplete choices and return them
        choices: list[Choice] = []
        for item in items:
            if isinstance(item, tuple):
                choices.append(
                    Choice(name=f"💬 {item[0]} → {item[1].key}", value=item[0])
                )
            else:
                choices.append(Choice(name=f"💬 {item.key}", value=item.key))
        return choices

    # @@ LISTENERS
    @Cog.listener()
    async def on_message(self, message: Message):
        # Make sure this message wasn't sent by the bot
        if is_bot(self.bot, message.author):
            return

        # Make sure the message was sent in a messageable channel in a guild
        if not (message.guild and isinstance(message.channel, Messageable)):
            return

        await self.state[message.guild].on_message(message)

    # @@ COMMANDS

    # @@ faq

    cmd_faq = Group(name="faq", description="Show FAQs", guild_only=True)

    # @@ faq get
    @cmd_faq.command(name="get", description="Get a frequently asked question (FAQ)")
    @describe(query="The FAQ to get")
    @autocomplete(query=faq_and_alias_autocomplete)
    async def cmd_faq_get(self, interaction: Interaction, query: str):
        assert isinstance(interaction.guild, Guild)
        await self.state[interaction.guild].get_faq(interaction, query)

    # @@ faq list
    @cmd_faq.command(name="list", description="List available FAQs")
    async def cmd_faq_list(self, interaction: Interaction):
        assert isinstance(interaction.guild, Guild)
        await self.state[interaction.guild].list_faqs(interaction)

    # @@ faqs

    cmd_faqs = Group(
        name="faqs",
        description="Manage FAQs",
        guild_only=True,
        default_permissions=Permissions(administrator=True),
    )

    # @@ faqs add
    @cmd_faqs.command(name="add", description="Add a new FAQ")
    async def cmd_faqs_add(self, interaction: Interaction):
        assert isinstance(interaction.guild, Guild)
        await self.state[interaction.guild].add_faq(interaction)

    # @@ faqs modify
    @cmd_faqs.command(name="modify", description="Modify a FAQ")
    @describe(faq="The FAQ to modify")
    @autocomplete(faq=faq_autocomplete)
    async def cmd_faqs_modify(self, interaction: Interaction, faq: str):
        assert isinstance(interaction.guild, Guild)
        await self.state[interaction.guild].modify_faq(interaction, faq)

    # @@ faqs remove
    @cmd_faqs.command(name="remove", description="Remove a FAQ")
    @describe(faq="The FAQ to remove")
    @autocomplete(faq=faq_autocomplete)
    async def cmd_faqs_remove(self, interaction: Interaction, faq: str):
        assert isinstance(interaction.guild, Guild)
        await self.state[interaction.guild].remove_faq(interaction, faq)

    # @@ faqs details
    @cmd_faqs.command(name="details", description="Show the details about a FAQ")
    @describe(faq="The FAQ to show details about")
    @autocomplete(faq=faq_autocomplete)
    async def cmd_faqs_details(self, interaction: Interaction, faq: str):
        assert isinstance(interaction.guild, Guild)
        await self.state[interaction.guild].show_faq_details(interaction, faq)

    # @@ faqs prefix-pattern

    cmd_faqs_prefix_pattern = Group(
        name="prefix-pattern",
        description="Manage the FAQ prefix pattern",
        parent=cmd_faqs,
    )

    # @@ faqs prefix-pattern set
    @cmd_faqs_prefix_pattern.command(
        name="set", description="Set the FAQ prefix pattern"
    )
    @describe(pattern="A regex pattern")
    async def cmd_faqs_prefix_pattern_set(self, interaction: Interaction, pattern: str):
        assert isinstance(interaction.guild, Guild)
        await self.state[interaction.guild].set_prefix_pattern(interaction, pattern)

    # @@ faqs prefix-pattern clear
    @cmd_faqs_prefix_pattern.command(
        name="clear", description="Clear the FAQ prefix pattern"
    )
    async def cmd_faqs_prefix_pattern_clear(self, interaction: Interaction):
        assert isinstance(interaction.guild, Guild)
        await self.state[interaction.guild].clear_prefix_pattern(interaction)

    # @@ faqs prefix-pattern show
    @cmd_faqs_prefix_pattern.command(
        name="show", description="Show the FAQ prefix pattern"
    )
    async def cmd_faqs_prefix_pattern_show(self, interaction: Interaction):
        assert isinstance(interaction.guild, Guild)
        await self.state[interaction.guild].show_prefix_pattern(interaction)

    # @@ faqs match-pattern

    cmd_faqs_match_pattern = Group(
        name="match-pattern",
        description="Manage the FAQ match pattern",
        parent=cmd_faqs,
    )

    # @@ faqs match-pattern set
    @cmd_faqs_match_pattern.command(name="set", description="Set the FAQ match pattern")
    @describe(pattern="A regex pattern")
    async def cmd_faqs_match_pattern_set(self, interaction: Interaction, pattern: str):
        assert isinstance(interaction.guild, Guild)
        await self.state[interaction.guild].set_match_pattern(interaction, pattern)

    # @@ faqs match-pattern clear
    @cmd_faqs_match_pattern.command(
        name="clear", description="Clear the FAQ match pattern"
    )
    async def cmd_faqs_match_pattern_clear(self, interaction: Interaction):
        assert isinstance(interaction.guild, Guild)
        await self.state[interaction.guild].clear_match_pattern(interaction)

    # @@ faqs match-pattern show
    @cmd_faqs_match_pattern.command(
        name="show", description="Show the FAQ match pattern"
    )
    async def cmd_faqs_match_pattern_show(self, interaction: Interaction):
        assert isinstance(interaction.guild, Guild)
        await self.state[interaction.guild].show_match_pattern(interaction)
