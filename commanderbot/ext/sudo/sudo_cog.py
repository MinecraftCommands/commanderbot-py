import importlib.util
import platform
from enum import Enum
from typing import Optional

import psutil
from discord import (
    AppInfo,
    Asset,
    Attachment,
    Embed,
    Emoji,
    Interaction,
    Object,
    Permissions,
)
from discord.app_commands import (
    AppCommand,
    AppCommandContext,
    AppInstallationType,
    Choice,
    Group,
    Transform,
    Transformer,
    autocomplete,
    describe,
)
from discord.ext.commands import Bot, Cog
from discord.utils import format_dt

from commanderbot.core.commander_bot import CommanderBot
from commanderbot.core.config import Config
from commanderbot.core.configured_extension import ConfiguredExtension
from commanderbot.core.exceptions import (
    ApplicationEmojiDoesNotExist,
    ExtensionIsRequired,
    ExtensionNotInConfig,
)
from commanderbot.core.utils import is_commander_bot
from commanderbot.ext.sudo.sudo_data import CogWithStore
from commanderbot.ext.sudo.sudo_exceptions import (
    BotHasNoAvatar,
    BotHasNoBanner,
    CannotFindApplicationEmoji,
    CannotManageExtensionNotInConfig,
    CannotManageRequiredExtension,
    CogHasNoStore,
    ErrorAddingApplicationEmoji,
    ErrorChangingBotAvatar,
    ErrorChangingBotBanner,
    ErrorRemovingApplicationEmoji,
    ErrorRenamingApplicationEmoji,
    ExtensionLoadError,
    ExtensionReloadError,
    ExtensionResolutionError,
    ExtensionUnloadError,
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


class ExtensionTransformer(Transformer):
    """
    A transformer that resolves `value` into a `ConfiguredExtension` from the config.
    """

    async def transform(
        self, interaction: Interaction[CommanderBot], value: str
    ) -> ConfiguredExtension:
        resolved_name: str = ""
        try:
            resolved_name = importlib.util.resolve_name(value, "commanderbot")
            return interaction.client.config.get_optional_extension(resolved_name)
        except ImportError as ex:
            raise ExtensionResolutionError(str(ex))
        except ExtensionNotInConfig:
            raise CannotManageExtensionNotInConfig(resolved_name)
        except ExtensionIsRequired:
            raise CannotManageRequiredExtension(resolved_name)


class EnabledExtensionTransformer(ExtensionTransformer):
    """
    Extends `ExtensionTransformer` to provide autocomplete for enabled extensions.
    """

    async def autocomplete(
        self, interaction: Interaction[CommanderBot], value: str
    ) -> list[Choice[str]]:
        config: Config = interaction.client.config
        choices: list[Choice] = []
        for ext in (ext for ext in config.enabled_extensions if not ext.required):
            if not value:
                choices.append(Choice(name=f"💿 {ext.name}", value=ext.name))
            elif value in ext.name:
                choices.append(Choice(name=f"💿 {ext.name}", value=ext.name))

        return choices[: constants.MAX_AUTOCOMPLETE_CHOICES]


class DisabledExtensionTransformer(ExtensionTransformer):
    """
    Extends `ExtensionTransformer` to provide autocomplete for disabled extensions.
    """

    async def autocomplete(
        self, interaction: Interaction[CommanderBot], value: str
    ) -> list[Choice[str]]:
        config: Config = interaction.client.config
        choices: list[Choice] = []
        for ext in (ext for ext in config.disabled_extensions if not ext.required):
            if not value:
                choices.append(Choice(name=f"💿 {ext.name}", value=ext.name))
            elif value in ext.name:
                choices.append(Choice(name=f"💿 {ext.name}", value=ext.name))

        return choices[: constants.MAX_AUTOCOMPLETE_CHOICES]


class ApplicationEmojiTransformer(Transformer):
    """
    A transformer that resolves `value` into an application emoji.
    """

    async def transform(
        self, interaction: Interaction[CommanderBot], value: str
    ) -> Emoji:
        try:
            return await interaction.client.application_emojis.fetch(value)
        except ApplicationEmojiDoesNotExist:
            raise CannotFindApplicationEmoji(value)

    async def autocomplete(
        self, interaction: Interaction[CommanderBot], value: str
    ) -> list[Choice[str]]:
        # Fetch all emojis
        emojis = await interaction.client.application_emojis.fetch_all()

        # Create choices
        choices: list[Choice] = []
        for emoji in emojis:
            if not value:
                choices.append(Choice(name=f"🎨 {emoji.name}", value=emoji.name))
            elif value in emoji.name:
                choices.append(Choice(name=f"🎨 {emoji.name}", value=emoji.name))

        return choices[: constants.MAX_AUTOCOMPLETE_CHOICES]


class SudoCog(Cog, name="commanderbot.ext.sudo"):
    def __init__(self, bot: Bot):
        self.bot: Bot = bot

        # Grab the current process and get its CPU usage to throw away the initial 0% usage.
        self.process: psutil.Process = psutil.Process()
        self.process.cpu_percent()

    # @@ UTILITIES

    async def _require_avatar(self) -> Asset:
        assert is_commander_bot(self.bot)
        if avatar := await self.bot.get_avatar():
            return avatar
        raise BotHasNoAvatar

    async def _require_banner(self) -> Asset:
        assert is_commander_bot(self.bot)
        if banner := await self.bot.get_banner():
            return banner
        raise BotHasNoBanner

    # @@ AUTOCOMPLETE

    async def cog_with_store_autocomplete(
        self, interaction: Interaction, value: str
    ) -> list[Choice[str]]:
        choices: list[Choice] = []
        for cog in self.bot.cogs.values():
            if isinstance(cog, CogWithStore):
                name: str = cog.qualified_name
                if not value:
                    choices.append(Choice(name=f"🛞 {name}", value=name))
                elif value in name:
                    choices.append(Choice(name=f"🛞 {name}", value=name))

        return choices[: constants.MAX_AUTOCOMPLETE_CHOICES]

    # @@ COMMANDS

    # @@ sudo

    cmd_sudo = Group(
        name="sudo",
        description="Commands for bot maintainers",
        allowed_installs=AppInstallationType(guild=True),
        allowed_contexts=AppCommandContext(
            guild=True, dm_channel=True, private_channel=True
        ),
        default_permissions=Permissions(administrator=True),
    )

    # @@ sudo appinfo
    @cmd_sudo.command(name="appinfo", description="Show the application info")
    @checks.is_owner()
    async def cmd_sudo_appinfo(self, interaction: Interaction):
        # Respond with a defer since getting the application info may take a while
        await interaction.response.defer(ephemeral=True)

        # Get the application info
        assert is_commander_bot(self.bot)
        app: AppInfo = await self.bot.application_info()

        owner: str = app.team.name if app.team else f"{app.owner.mention} ({app.owner})"
        has_app_commands: str = "✅" if app.flags.app_commands_badge else "❌"
        public_bot: str = "✅" if app.bot_public else "❌"

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

        cpu_usage: float = 0.0
        if (cpu_cores := psutil.cpu_count()) and cpu_cores > 0:
            cpu_usage = self.process.cpu_percent() / cpu_cores

        memory_usage: float = utils.bytes_to(
            self.process.memory_full_info().uss, utils.SizeUnit.MEGABYTE, binary=True
        )

        # Create embed fields
        installs_field = (
            f"Public Bot: {public_bot}",
            f"Guilds: `{app.approximate_guild_count}`",
            f"Users: `{app.approximate_user_install_count}`",
        )

        emojis_field = f"Total: `{len(self.bot.application_emojis.get_all())}/{constants.MAX_APPLICATION_EMOJIS}`"

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
            f"Python Version: `{constants.PYTHON_VERSION}`",
            f"CPU: `{cpu_usage:.2f}%`",
            f"RAM: `{memory_usage:.2f} MB`",
        )

        fields = {
            "Owner": owner,
            "Flags": f"`{app.flags.value}`",
            "Message Content": message_content_enabled,
            "Guild Members": guild_members_enabled,
            "Presence": presence_enabled,
            "Installs": "\n".join(installs_field),
            "Emojis": emojis_field,
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

        await interaction.followup.send(embed=embed, ephemeral=True)

    # @@ sudo extension

    cmd_sudo_extension = Group(
        name="extension", description="Manage the bot's extensions", parent=cmd_sudo
    )

    # @@ sudo extension load
    @cmd_sudo_extension.command(name="load", description="Load an extension")
    @describe(extension="The extension to load")
    @checks.is_owner()
    async def cmd_sudo_extension_load(
        self,
        interaction: Interaction,
        extension: Transform[ConfiguredExtension, DisabledExtensionTransformer],
    ):
        # Respond with a defer since loading the extension might take a while
        await interaction.response.defer(ephemeral=True)

        # Try to load the extension
        try:
            await self.bot.load_extension(extension.name)
            await interaction.followup.send(
                f"✅ Loaded extension `{extension.name}`", ephemeral=True
            )
        except Exception as ex:
            raise ExtensionLoadError(extension.name, str(ex))

    # @@ sudo extension unload
    @cmd_sudo_extension.command(name="unload", description="Unload an extension")
    @describe(extension="The extension to unload")
    @checks.is_owner()
    async def cmd_sudo_extension_unload(
        self,
        interaction: Interaction,
        extension: Transform[ConfiguredExtension, EnabledExtensionTransformer],
    ):
        # Respond with a defer since unloading the extension might take a while
        await interaction.response.defer(ephemeral=True)

        # Try to unload the extension
        try:
            await self.bot.unload_extension(extension.name)
            await interaction.followup.send(
                f"⛔ Unloaded extension `{extension.name}`", ephemeral=True
            )
        except Exception as ex:
            raise ExtensionUnloadError(extension.name, str(ex))

    # @@ sudo extension reload
    @cmd_sudo_extension.command(name="reload", description="Reload an extension")
    @describe(extension="The extension to reload")
    @checks.is_owner()
    async def cmd_sudo_extension_reload(
        self,
        interaction: Interaction,
        extension: Transform[ConfiguredExtension, EnabledExtensionTransformer],
    ):
        # Respond with a defer since reloading the extension might take a while
        await interaction.response.defer(ephemeral=True)

        # Try to reload the extension
        try:
            await self.bot.reload_extension(extension.name)
            await interaction.followup.send(
                f"♻️ Reloaded extension `{extension.name}`", ephemeral=True
            )
        except Exception as ex:
            raise ExtensionReloadError(extension.name, str(ex))

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

    cmd_sudo_export = Group(
        name="export", description="Export data from the bot", parent=cmd_sudo
    )

    # @@ sudo export config
    @cmd_sudo_export.command(name="config", description="Export the bot's config")
    @checks.is_owner()
    async def cmd_sudo_export_config(self, interaction: Interaction):
        # Respond with a defer since exporting the config might take a while
        await interaction.response.defer(ephemeral=True)

        # Turn the config into Json
        assert is_commander_bot(self.bot)
        json_data: str = json_dumps(self.bot.config.to_json())
        file = utils.str_to_file(json_data, "config.json")

        # Respond with the config file
        await interaction.followup.send(
            "⚙️ Exported the bot's config:", file=file, ephemeral=True
        )

    # @@ sudo export database
    @cmd_sudo_export.command(name="database", description="Export a cog's database")
    @describe(cog="A cog with a database")
    @autocomplete(cog=cog_with_store_autocomplete)
    @checks.is_owner()
    async def cmd_sudo_export_database(self, interaction: Interaction, cog: str):
        # Respond with a defer since exporting the database might take a while
        await interaction.response.defer(ephemeral=True)

        # Try to get the cog
        found_cog = self.bot.get_cog(cog)
        if not found_cog:
            raise UnknownCog(cog)
        elif not isinstance(found_cog, CogWithStore):
            raise CogHasNoStore(found_cog.qualified_name)

        # Export the store and respond with a followup
        match found_cog.store.db:
            case JsonFileDatabaseAdapter() as db:
                cache = await db.get_cache()
                json_data = json_dumps(db.serializer(cache))
                file = utils.str_to_file(json_data, f"{found_cog.qualified_name}.json")
                await interaction.followup.send(
                    f"📦 Exported Json store for `{found_cog.qualified_name}`:",
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
        avatar: Asset = await self._require_avatar()
        await interaction.followup.send(
            f"✅ Set the bot's avatar to:\n{avatar.url}", ephemeral=True
        )

    # @@ sudo avatar clear
    @cmd_sudo_avatar.command(name="clear", description="Clear the bot's avatar")
    @checks.is_owner()
    async def cmd_sudo_avatar_clear(self, interaction: Interaction):
        # Respond with a defer since clearing the avatar may take a while
        await interaction.response.defer(ephemeral=True)

        # The bot must have an avatar
        await self._require_avatar()

        # Respond with a confirmation dialog
        result = await respond_with_confirmation(
            interaction,
            f"Are you sure you want to clear the bot's avatar?",
            ephemeral=True,
        )
        match result:
            case ConfirmationResult.YES:
                try:
                    assert is_commander_bot(self.bot)
                    await self.bot.clear_avatar()
                    await interaction.followup.send(
                        "✅ Cleared the bot's avatar", ephemeral=True
                    )
                except Exception as ex:
                    await interaction.delete_original_response()
                    raise ErrorChangingBotAvatar(str(ex))
            case _:
                await interaction.followup.send(
                    "Keeping the bot's current avatar", ephemeral=True
                )

    # @@ sudo avatar show
    @cmd_sudo_avatar.command(name="show", description="Show the bot's avatar")
    @checks.is_owner()
    async def cmd_sudo_avatar_show(self, interaction: Interaction):
        # Respond with a defer since fetching the avatar may take a while
        await interaction.response.defer(ephemeral=True)

        # Show the current avatar
        avatar: Asset = await self._require_avatar()
        await interaction.followup.send(
            f"🖼️ The bot's current avatar is:\n{avatar.url}", ephemeral=True
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
        banner: Asset = await self._require_banner()
        await interaction.followup.send(
            f"✅ Set the bot's banner to:\n{banner.url}", ephemeral=True
        )

    # @@ sudo banner clear
    @cmd_sudo_banner.command(name="clear", description="Clear the bot's banner")
    @checks.is_owner()
    async def cmd_sudo_banner_clear(self, interaction: Interaction):
        # Respond with a defer since clearing the banner may take a while
        await interaction.response.defer(ephemeral=True)

        # The bot must have a banner
        await self._require_banner()

        # Respond with a confirmation dialog
        result = await respond_with_confirmation(
            interaction,
            f"Are you sure you want to clear the bot's banner?",
            ephemeral=True,
        )
        match result:
            case ConfirmationResult.YES:
                try:
                    assert is_commander_bot(self.bot)
                    await self.bot.clear_banner()
                    await interaction.followup.send(
                        "✅ Cleared the bot's banner", ephemeral=True
                    )
                except Exception as ex:
                    await interaction.delete_original_response()
                    raise ErrorChangingBotBanner(str(ex))
            case _:
                await interaction.followup.send(
                    "Keeping the bot's current banner", ephemeral=True
                )

    # @@ sudo banner show
    @cmd_sudo_banner.command(name="show", description="Show the bot's banner")
    @checks.is_owner()
    async def cmd_sudo_banner_show(self, interaction: Interaction):
        # Respond with a defer since fetching the banner may take a while
        await interaction.response.defer(ephemeral=True)

        # Show the current banner
        banner: Asset = await self._require_banner()
        await interaction.followup.send(
            f"🖼️ The bot's current banner is:\n{banner.url}", ephemeral=True
        )

    # @@ sudo emoji

    cmd_sudo_emoji = Group(
        name="emoji", description="Manage the bot's application emojis", parent=cmd_sudo
    )

    # @@ sudo emoji add
    @cmd_sudo_emoji.command(name="add", description="Add an application emoji")
    @describe(
        name="The name for this application emoji",
        file="The image for this application emoji",
    )
    @checks.is_owner()
    async def cmd_sudo_emoji_add(
        self, interaction: Interaction, name: str, file: Attachment
    ):
        # Respond with a defer since adding the application emoji may take a while
        await interaction.response.defer(ephemeral=True)

        # Add the application emoji
        try:
            assert is_commander_bot(self.bot)
            created_emoji: Emoji = await self.bot.application_emojis.create(name, file)
        except Exception as ex:
            raise ErrorAddingApplicationEmoji(str(ex))

        # Show the newly added application emoji
        await interaction.followup.send(
            f"✅ Added application emoji `{created_emoji.name}` ({created_emoji})",
            ephemeral=True,
        )

    # @@ sudo emoji rename
    @cmd_sudo_emoji.command(name="rename", description="Rename an application emoji")
    @describe(
        emoji="The application emoji to rename",
        new_name="The new name for this application emoji",
    )
    @checks.is_owner()
    async def cmd_sudo_emoji_rename(
        self,
        interaction: Interaction,
        emoji: Transform[Emoji, ApplicationEmojiTransformer],
        new_name: str,
    ):
        # Respond with a defer since renaming the application emoji may take a while
        await interaction.response.defer(ephemeral=True)

        # Rename the application emoji
        try:
            assert is_commander_bot(self.bot)
            modified_emoji: Emoji = await self.bot.application_emojis.edit(
                emoji.name, new_name
            )
        except Exception as ex:
            raise ErrorRenamingApplicationEmoji(str(ex))

        # Respond that the emoji was renamed
        await interaction.followup.send(
            f"✅ Renamed application emoji `{emoji.name}` to `{modified_emoji.name}`"
        )

    # @@ sudo emoji remove
    @cmd_sudo_emoji.command(name="remove", description="Remove an application emoji")
    @describe(emoji="The application emoji to remove")
    @checks.is_owner()
    async def cmd_sudo_emoji_remove(
        self,
        interaction: Interaction,
        emoji: Transform[Emoji, ApplicationEmojiTransformer],
    ):
        # Respond with a defer since removing the application emoji may take a while
        await interaction.response.defer(ephemeral=True)

        # Respond with a confirmation dialog
        result = await respond_with_confirmation(
            interaction,
            f"Are you sure you want to remove the application emoji `{emoji.name}` ({emoji})?",
            ephemeral=True,
        )
        match result:
            case ConfirmationResult.YES:
                try:
                    assert is_commander_bot(self.bot)
                    await self.bot.application_emojis.delete(emoji.name)
                    await interaction.followup.send(
                        f"Removed application emoji `{emoji.name}`", ephemeral=True
                    )
                except Exception as ex:
                    await interaction.delete_original_response()
                    raise ErrorRemovingApplicationEmoji(str(ex))
            case _:
                await interaction.followup.send(
                    f"Keeping application emoji `{emoji.name}` ({emoji})",
                    ephemeral=True,
                )

    # @@ sudo emoji details
    @cmd_sudo_emoji.command(
        name="details", description="Show the details about an application emoji"
    )
    @describe(emoji="The application emoji to show details about")
    @checks.is_owner()
    async def cmd_sudo_emoji_details(
        self,
        interaction: Interaction,
        emoji: Transform[Emoji, ApplicationEmojiTransformer],
    ):
        # Respond with a defer since fetching the emojis may take a while
        await interaction.response.defer(ephemeral=True)

        # Create application emoji details embed
        embed = Embed(
            title=f"Details for application emoji `{emoji.name}`",
            description=f"**Preview**\n> {emoji}",
            color=0x00ACED,
        )
        embed.add_field(name="Name", value=f"`{emoji.name}`")
        embed.add_field(name="ID", value=f"`{emoji.id}`")
        if emoji.user:
            embed.add_field(
                name="Added By",
                value=f"<@{emoji.user.id}> ({format_dt(emoji.created_at, style='R')})",
            )

        await interaction.followup.send(embed=embed, ephemeral=True)

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
            f"✅ Synced `{len(synced_commands)}` app commands to {syncing_to_msg}",
            ephemeral=True,
        )
