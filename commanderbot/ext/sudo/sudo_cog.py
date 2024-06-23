import platform
from enum import Enum
from typing import Optional

import psutil
from discord import AppInfo, Asset, Attachment, Embed, Interaction, Object, Permissions
from discord.app_commands import AppCommand, Choice, Group, autocomplete, describe
from discord.ext.commands import Bot, Cog

from commanderbot.core.utils import is_commander_bot
from commanderbot.ext.sudo.sudo_data import CogWithStore
from commanderbot.ext.sudo.sudo_exceptions import (
    BotHasNoAvatar,
    BotHasNoBanner,
    CogHasNoStore,
    ErrorChangingBotAvatar,
    ErrorChangingBotBanner,
    GlobalSyncError,
    GuildIDNotFound,
    GuildSyncError,
    UnknownCog,
    UnsupportedStoreExport,
)
from commanderbot.lib import (
    ConfirmationResult,
    constants,
    json_dumps,
    respond_with_confirmation,
    utils,
)
from commanderbot.lib.app_commands import checks
from commanderbot.lib.cogs.database import JsonFileDatabaseAdapter


class SyncTypeChoices(Enum):
    sync_only = 0
    copy = 1
    remove = 2


class SudoCog(Cog, name="commanderbot.ext.sudo"):
    def __init__(self, bot: Bot):
        self.bot: Bot = bot

        # Grab the current process and get its CPU usage to throw away the initial 0% usage.
        self.process: psutil.Process = psutil.Process()
        self.process.cpu_percent()

    # @@ AUTOCOMPLETE
    async def cog_with_store_autocomplete(
        self, interaction: Interaction, value: str
    ) -> list[Choice[str]]:
        choices: list[Choice] = []
        for cog in self.bot.cogs.values():
            if isinstance(cog, CogWithStore):
                name: str = cog.qualified_name
                if not value:
                    choices.append(Choice(name=name, value=name))
                elif value in name:
                    choices.append(Choice(name=name, value=name))

        return choices

    async def _require_avatar(self, bot: Bot) -> Asset:
        assert is_commander_bot(bot)
        if avatar := await bot.get_avatar():
            return avatar
        raise BotHasNoAvatar

    async def _require_banner(self, bot: Bot) -> Asset:
        assert is_commander_bot(bot)
        if banner := await bot.get_banner():
            return banner
        raise BotHasNoBanner

    # @@ COMMANDS

    # @@ sudo

    cmd_sudo = Group(
        name="sudo",
        description="Commands for bot maintainers",
        default_permissions=Permissions(administrator=True),
    )

    # @@ sudo appinfo
    @cmd_sudo.command(name="appinfo", description="Show the application info")
    @checks.is_owner()
    async def cmd_sudo_appinfo(self, interaction: Interaction):
        # Get app info
        app: AppInfo = await self.bot.application_info()

        owner: str = app.team.name if app.team else f"{app.owner.mention} ({app.owner})"
        has_app_commands: str = "✅" if app.flags.app_commands_badge else "❌"
        message_content_enabled: str = "❌"
        if app.flags.gateway_message_content:
            message_content_enabled = "✅"
        elif app.flags.gateway_message_content_limited:
            message_content_enabled = "✅ (Limited)"

        guild_members_enabled: str = "❌"
        if app.flags.gateway_guild_members:
            guild_members_enabled = "✅"
        elif app.flags.gateway_guild_members_limited:
            guild_members_enabled = "✅ (Limited)"

        presence_enabled: str = "❌"
        if app.flags.gateway_presence:
            presence_enabled = "✅"
        elif app.flags.gateway_presence_limited:
            presence_enabled = "✅ (Limited)"

        # Get basic info on the running process
        uname = platform.uname()
        ptr_size: int = constants.POINTER_SIZE_BITS

        architecture: str = "x86" if ptr_size == 32 else f"x{ptr_size}"
        cpu_usage: float = self.process.cpu_percent() / psutil.cpu_count()
        memory_usage: float = utils.bytes_to(
            self.process.memory_full_info().uss, utils.SizeUnit.MEGABYTE, binary=True
        )

        # Create embed fields
        commands_field = (
            f"Total: `{len(self.bot.commands)}`",
            f"Prefix: `{self.bot.command_prefix}`",
        )

        app_commands_field = (
            f"Total: `{len(self.bot.tree.get_commands())}`",
            f"Global Commands: {has_app_commands}",
        )

        system_field = (
            f"OS: `{uname.system} {architecture}`",
            f"Version: `{uname.version}`",
        )

        process_field = (
            f"CPU: `{cpu_usage:.2f}%`",
            f"RAM: `{memory_usage:.2f} MiB`",
        )

        fields = {
            "Owner": owner,
            "Flags": f"`{app.flags.value}`",
            "Message Content": message_content_enabled,
            "Guild Members": guild_members_enabled,
            "Presence": presence_enabled,
            "Commands": "\n".join(commands_field),
            "App Commands": "\n".join(app_commands_field),
            "System": "\n".join(system_field),
            "Process": "\n".join(process_field),
        }

        # Create embed and add fields
        embed: Embed = Embed(
            title=app.name, description=app.description, color=0x00ACED
        )

        embed.set_thumbnail(url=app.icon.url if app.icon else None)
        for k, v in fields.items():
            embed.add_field(name=k, value=v)

        await interaction.response.send_message(embed=embed, ephemeral=True)

    # @@ sudo shutdown
    @cmd_sudo.command(name="shutdown", description="Shut down the bot")
    @checks.is_owner()
    async def cmd_sudo_shutdown(self, interaction: Interaction):
        result = await respond_with_confirmation(
            interaction, "Are you sure you want to shut down the bot?", ephemeral=True
        )
        match result:
            case ConfirmationResult.YES:
                await interaction.followup.send("😴 Shutting down...", ephemeral=True)
                await self.bot.close()
            case ConfirmationResult.NO | ConfirmationResult.NO_RESPONSE:
                await interaction.followup.send("🙂 Continuing...", ephemeral=True)

    # @@ sudo export
    @cmd_sudo.command(name="export", description="Export a cog's store")
    @describe(cog="The cog to export")
    @autocomplete(cog=cog_with_store_autocomplete)
    @checks.is_owner()
    async def cmd_sudo_export(self, interaction: Interaction, cog: str):
        # Respond with a defer since exporting the data might take a while
        await interaction.response.defer(ephemeral=True)

        # Try to get the cog
        found_cog = self.bot.get_cog(cog)
        if not found_cog:
            raise UnknownCog(cog)
        elif not isinstance(found_cog, CogWithStore):
            raise CogHasNoStore(found_cog)

        # Esport the store and respond with a followup
        match found_cog.store.db:
            case JsonFileDatabaseAdapter() as db:
                cache = await db.get_cache()
                json_data = json_dumps(db.serializer(cache))
                file = utils.str_to_file(json_data, f"{found_cog.qualified_name}.json")
                await interaction.followup.send(
                    f"Exported Json store for `{found_cog.qualified_name}`",
                    file=file,
                    ephemeral=True,
                )
            case _ as db:
                raise UnsupportedStoreExport(db)

    # @@ sudo avatar

    cmd_sudo_avatar = Group(
        name="avatar", description="Manage the bot's avatar", parent=cmd_sudo
    )

    # @@ sudo avatar set
    @cmd_sudo_avatar.command(name="set", description="Set the bot's avatar")
    @describe(file="The new avatar")
    @checks.is_owner()
    async def cmd_sudo_avatar_set(self, interaction: Interaction, file: Attachment):
        # Respond with a defer since uploading the file may take a while
        await interaction.response.defer(ephemeral=True)

        # Set the new avatar
        try:
            assert is_commander_bot(self.bot)
            await self.bot.set_avatar(file)
        except Exception as ex:
            raise ErrorChangingBotAvatar(str(ex))

        # Show the new avatar
        avatar: Asset = await self._require_avatar(self.bot)
        await interaction.followup.send(
            f"Set the bot's avatar to:\n{avatar.url}", ephemeral=True
        )

    # @@ sudo avatar clear
    @cmd_sudo_avatar.command(name="clear", description="Clear the bot's avatar")
    @checks.is_owner()
    async def cmd_sudo_avatar_clear(self, interaction: Interaction):
        # Respond with a defer since clearing the avatar may take a while
        await interaction.response.defer(ephemeral=True)

        # The bot must have an avatar
        await self._require_avatar(self.bot)

        # Clear the avatar
        try:
            assert is_commander_bot(self.bot)
            await self.bot.set_avatar(None)
        except Exception as ex:
            raise ErrorChangingBotAvatar(str(ex))

        # Send a response that the avatar has been cleared
        await interaction.followup.send("Cleared the bot's avatar", ephemeral=True)

    # @@ sudo avatar show
    @cmd_sudo_avatar.command(name="show", description="Snow the bot's avatar")
    @checks.is_owner()
    async def cmd_sudo_avatar_show(self, interaction: Interaction):
        # Respond with a defer since fetching the avatar may take a while
        await interaction.response.defer(ephemeral=True)

        # Show the current avatar
        avatar: Asset = await self._require_avatar(self.bot)
        await interaction.followup.send(
            f"The bot's current avatar is:\n{avatar.url}", ephemeral=True
        )

    # @@ sudo banner

    cmd_sudo_banner = Group(
        name="banner", description="Manage the bot's banner", parent=cmd_sudo
    )

    # @@ sudo banner set
    @cmd_sudo_banner.command(name="set", description="Set the bot's banner")
    @describe(file="The new banner")
    @checks.is_owner()
    async def cmd_sudo_banner_set(self, interaction: Interaction, file: Attachment):
        # Respond with a defer since uploading the file may take a while
        await interaction.response.defer(ephemeral=True)

        # Set the new banner
        try:
            assert is_commander_bot(self.bot)
            await self.bot.set_banner(file)
        except Exception as ex:
            raise ErrorChangingBotBanner(str(ex))

        # Show the new banner
        banner: Asset = await self._require_banner(self.bot)
        await interaction.followup.send(
            f"Set the bot's banner to:\n{banner.url}", ephemeral=True
        )

    # @@ sudo banner clear
    @cmd_sudo_banner.command(name="clear", description="Clear the bot's banner")
    @checks.is_owner()
    async def cmd_sudo_banner_clear(self, interaction: Interaction):
        # Respond with a defer since clearing the banner may take a while
        await interaction.response.defer(ephemeral=True)

        # The bot must have a banner
        await self._require_banner(self.bot)

        # Clear the
        try:
            assert is_commander_bot(self.bot)
            await self.bot.set_banner(None)
        except Exception as ex:
            raise ErrorChangingBotBanner(str(ex))

        # Send a response that the banner has been cleared
        await interaction.followup.send("Cleared the bot's banner", ephemeral=True)

    # @@ sudo banner show
    @cmd_sudo_banner.command(name="show", description="Show the bot's banner")
    @checks.is_owner()
    async def cmd_sudo_banner_show(self, interaction: Interaction):
        # Respond with a defer since fetching the banner may take a while
        await interaction.response.defer(ephemeral=True)

        # Show the current banner
        banner: Asset = await self._require_banner(self.bot)
        await interaction.followup.send(
            f"The bot's current banner is:\n{banner.url}", ephemeral=True
        )

    # @@ sudo sync

    cmd_sudo_sync = Group(name="sync", description="Sync app commands", parent=cmd_sudo)

    # @@ sudo sync global
    @cmd_sudo_sync.command(name="global", description="Sync global app commands")
    @checks.is_owner()
    async def cmd_sudo_sync_global(self, interaction: Interaction):
        # Respond with a defer since syncing the commands may take a while
        await interaction.response.defer(ephemeral=True)

        # Try to sync app commands
        synced_commands: list[AppCommand] = []
        try:
            synced_commands = await self.bot.tree.sync()
        except Exception as ex:
            raise GlobalSyncError(str(ex))

        # Send followup with sync results
        await interaction.followup.send(
            f"✅ Synced `{len(synced_commands)}` app commands globally", ephemeral=True
        )

    # @@ sudo sync guild
    @cmd_sudo_sync.command(name="guild", description="Sync app commands to a guild")
    @describe(
        sync_type="What action to take when syncing the commands",
        guild_id="The guild to sync (If not provided, the guild that the command was ran in is used instead)",
    )
    @checks.is_owner()
    async def cmd_sudo_sync_guild(
        self,
        interaction: Interaction,
        sync_type: SyncTypeChoices,
        guild_id: Optional[int],
    ):
        # Get the guild to sync to
        guild: Optional[Object] = None
        syncing_to_msg: Optional[str] = None
        if guild_id:
            guild = Object(guild_id)
            syncing_to_msg = f"guild `{guild.id}`"
        elif interaction.guild_id:
            guild = Object(interaction.guild_id)
            syncing_to_msg = "the current guild"
        else:
            raise GuildIDNotFound

        # Respond with a defer since syncing the commands may take a while
        await interaction.response.defer(ephemeral=True)

        # Try to sync app commands
        synced_commands: list[AppCommand] = []
        try:
            match sync_type:
                case SyncTypeChoices.sync_only:
                    synced_commands = await self.bot.tree.sync(guild=guild)
                case SyncTypeChoices.copy:
                    self.bot.tree.copy_global_to(guild=guild)
                    synced_commands = await self.bot.tree.sync(guild=guild)
                case SyncTypeChoices.remove:
                    self.bot.tree.clear_commands(guild=guild)
                    synced_commands = await self.bot.tree.sync(guild=guild)
        except Exception as ex:
            raise GuildSyncError(guild, str(ex))

        # Send followup with sync results
        await interaction.followup.send(
            f"Synced `{len(synced_commands)}` app commands to {syncing_to_msg}",
            ephemeral=True,
        )
