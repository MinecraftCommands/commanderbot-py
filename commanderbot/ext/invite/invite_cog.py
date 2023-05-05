from discord import Guild, Interaction, Permissions
from discord.app_commands import Choice, Group, autocomplete, describe
from discord.ext.commands import Bot, Cog

from commanderbot.ext.invite.invite_data import InviteData
from commanderbot.ext.invite.invite_guild_state import InviteGuildState
from commanderbot.ext.invite.invite_json_store import InviteJsonStore
from commanderbot.ext.invite.invite_options import InviteOptions
from commanderbot.ext.invite.invite_state import InviteState
from commanderbot.ext.invite.invite_store import InviteEntry, InviteStore
from commanderbot.lib import MAX_AUTOCOMPLETE_CHOICES
from commanderbot.lib.cogs import CogGuildStateManager
from commanderbot.lib.cogs.database import (
    InMemoryDatabaseOptions,
    JsonFileDatabaseAdapter,
    JsonFileDatabaseOptions,
    UnsupportedDatabaseOptions,
)
from commanderbot.lib.utils import async_expand


def _make_store(bot: Bot, cog: Cog, options: InviteOptions) -> InviteStore:
    db_options = options.database
    if isinstance(db_options, InMemoryDatabaseOptions):
        return InviteData()
    if isinstance(db_options, JsonFileDatabaseOptions):
        return InviteJsonStore(
            bot=bot,
            cog=cog,
            db=JsonFileDatabaseAdapter(
                options=db_options,
                serializer=lambda cache: cache.to_json(),
                deserializer=InviteData.from_data,
            ),
        )
    raise UnsupportedDatabaseOptions(db_options)


class InviteCog(Cog, name="commanderbot.ext.invite"):
    def __init__(self, bot: Bot, **options):
        self.bot: Bot = bot
        self.options = InviteOptions.from_data(options)
        self.store: InviteStore = _make_store(self.bot, self, self.options)
        self.state = InviteState(
            bot=self.bot,
            cog=self,
            guilds=CogGuildStateManager(
                bot=self.bot,
                cog=self,
                factory=lambda guild: InviteGuildState(
                    bot=self.bot, cog=self, guild=guild, store=self.store
                ),
            ),
            store=self.store,
        )

    # @@ AUTOCOMPLETE

    async def invite_key_autocomplete(
        self, interaction: Interaction, value: str
    ) -> list[Choice[str]]:
        """
        An autocomplete callback that will return any invites that match `value`
        """

        # Get all invites filtered by `value`
        assert isinstance(interaction.guild, Guild)
        filtered_invites: list[InviteEntry] = await async_expand(
            self.store.get_invites(interaction.guild, invite_filter=value.lower())
        )

        # Create a list of autocomplete choices and return them
        choices: list[Choice] = []
        for i, entry in enumerate(filtered_invites):
            if i == MAX_AUTOCOMPLETE_CHOICES:
                break
            choices.append(Choice(name=f"🔑 {entry.key}", value=entry.key))

        return choices

    # @@ COMMANDS

    # @@ invite

    # @@ invites

    cmd_invites = Group(
        name="invites",
        description="Manage invites",
        guild_only=True,
        default_permissions=Permissions(administrator=True),
    )

    # @@ invites add
    @cmd_invites.command(name="add", description="Add a new invite")
    async def cmd_invites_add(self, interaction: Interaction):
        assert isinstance(interaction.guild, Guild)
        await self.state[interaction.guild].add_invite(interaction)

    # @@ invites modify
    @cmd_invites.command(name="modify", description="Modify an invite")
    @describe(invite="The invite to modify")
    @autocomplete(invite=invite_key_autocomplete)
    async def cmd_invites_modify(self, interaction: Interaction, invite: str):
        assert isinstance(interaction.guild, Guild)
        await self.state[interaction.guild].modify_invite(interaction, invite)

    # @@ invites remove
    @cmd_invites.command(name="remove", description="Remove an invite")
    @describe(invite="The invite to remove")
    @autocomplete(invite=invite_key_autocomplete)
    async def cmd_invites_remove(self, interaction: Interaction, invite: str):
        assert isinstance(interaction.guild, Guild)
        await self.state[interaction.guild].remove_invite(interaction, invite)

    # @@ invites details
    @cmd_invites.command(name="details", description="Show the details of an invite")
    @describe(invite="The invite to show details about")
    @autocomplete(invite=invite_key_autocomplete)
    async def cmd_invites_details(self, interaction: Interaction, invite: str):
        assert isinstance(interaction.guild, Guild)
        await self.state[interaction.guild].show_invite_details(interaction, invite)

    # @@ invites here
    cmd_invites_here = Group(
        name="here", description="Manage guild invite", parent=cmd_invites
    )

    # @@ invites here set
    @cmd_invites_here.command(name="set", description="Set the invite for this guild")
    @describe(invite="The invite to set as the invite for this guild")
    @autocomplete(invite=invite_key_autocomplete)
    async def cmd_invites_here_set(self, interaction: Interaction, invite: str):
        assert isinstance(interaction.guild, Guild)
        await self.state[interaction.guild].set_guild_invite(interaction, invite)

    # @@ invites here clear
    @cmd_invites_here.command(
        name="clear", description="Clear the invite for this guild"
    )
    async def cmd_invites_here_clear(self, interaction: Interaction):
        assert isinstance(interaction.guild, Guild)
        await self.state[interaction.guild].clear_guild_invite(interaction)

    # @@ invites here show
    @cmd_invites_here.command(name="show", description="Show the invite for this guild")
    async def cmd_invites_here_show(self, interaction: Interaction):
        assert isinstance(interaction.guild, Guild)
        await self.state[interaction.guild].show_guild_invite(interaction)
