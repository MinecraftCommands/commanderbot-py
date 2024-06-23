import sys
from datetime import datetime, timedelta
from logging import Logger, getLogger
from typing import Any, Optional

from discord import Asset, Attachment, User
from discord.ext.commands import Bot, Context
from discord.interactions import Interaction
from discord.utils import utcnow

from commanderbot.core.exceptions import NotLoggedIn
from commanderbot.core.command_tree import CachingCommandTree
from commanderbot.core.configured_extension import ConfiguredExtension
from commanderbot.core.error_handling import (
    AppCommandErrorHandler,
    CommandErrorHandler,
    ErrorHandling,
    EventErrorHandler,
)
from commanderbot.core.help_command import HelpCommand
from commanderbot.lib import AllowedMentions, EventData, Intents


class CommanderBot(Bot):
    def __init__(self, *args, **kwargs):
        # Account for options that don't belong to the discord.py Bot base.
        self._extensions_data = kwargs.pop("extensions", None)
        self._sync_tree_on_login = kwargs.pop("sync_tree", False)

        # Account for options that need further processing.
        intents = Intents.default()
        if i := Intents.from_field_optional(kwargs, "intents"):
            intents = Intents.default() & i
        if i := Intents.from_field_optional(kwargs, "privileged_intents"):
            intents |= Intents.privileged() & i

        allowed_mentions = AllowedMentions.from_field_optional(
            kwargs, "allowed_mentions"
        )

        # Update kwargs after options have been further processed.
        kwargs.update(
            intents=intents,
            allowed_mentions=allowed_mentions or AllowedMentions.not_everyone(),
            help_command=HelpCommand(),
            tree_cls=CachingCommandTree,
        )

        # Initialize discord.py Bot base.
        super().__init__(*args, **kwargs)

        # Grab our own logger instance.
        self.log: Logger = getLogger("CommanderBot")

        # Remember when we started and the last time we connected.
        self._started_at: datetime = utcnow()
        self._connected_since: Optional[datetime] = None

        # Create an error handling component.
        self.error_handling = ErrorHandling(log=self.log)
        self.tree.on_error = self.on_app_command_error

        # Warn about a lack of configured intents.
        if intents is None:
            self.log.warning(
                f"No intents configured; using default flags: {self.intents.value}"
            )
        else:
            self.log.info(f"Using intents flags: {self.intents.value}")

        # Configure extensions.
        self.configured_extensions: dict[str, ConfiguredExtension] = {}

    async def _configure_extensions(self, extensions_data: list):
        if not isinstance(extensions_data, list):
            raise ValueError(f"Invalid extensions: {extensions_data}")

        self.log.info(f"Processing {len(extensions_data)} extensions...")

        all_extensions: list[ConfiguredExtension] = [
            ConfiguredExtension.from_data(entry) for entry in extensions_data
        ]

        self.configured_extensions = {}
        for ext in all_extensions:
            self.configured_extensions[ext.name] = ext

        enabled_extensions: list[ConfiguredExtension] = [
            ext for ext in all_extensions if not ext.disabled
        ]

        self.log.info(f"Loading {len(enabled_extensions)} enabled extensions...")

        for ext in enabled_extensions:
            self.log.info(f"[->] {ext.name}")
            try:
                await self.load_extension(ext.name)
            except:
                self.log.exception(f"Failed to load extension: {ext.name}")

        self.log.info(f"Finished loading extensions.")

    @property
    def started_at(self) -> datetime:
        return self._started_at

    @property
    def connected_since(self) -> Optional[datetime]:
        return self._connected_since

    @property
    def uptime(self) -> Optional[timedelta]:
        if self.connected_since is not None:
            return utcnow() - self.connected_since

    @property
    def command_tree(self) -> CachingCommandTree:
        # A hack to get the actual app command tree type for type checkers
        return self.tree  # type: ignore

    def get_extension_options(self, ext_name: str) -> Optional[dict[str, Any]]:
        if configured_extension := self.configured_extensions.get(ext_name):
            return configured_extension.options

    def add_event_error_handler(self, handler: EventErrorHandler):
        self.error_handling.add_event_error_handler(handler)

    def add_command_error_handler(self, handler: CommandErrorHandler):
        self.error_handling.add_command_error_handler(handler)

    def add_app_command_error_handler(self, handler: AppCommandErrorHandler):
        self.error_handling.add_app_command_error_handler(handler)

    async def set_avatar(self, new_avatar: Optional[bytes | Attachment]):
        # Throw exception if the bot isn't logged in
        if not self.user:
            raise NotLoggedIn

        # Read the attachment if necessary or just store the byte array
        data: Optional[bytes] = None
        if isinstance(new_avatar, Attachment):
            data = await new_avatar.read()
        else:
            data = new_avatar

        # Set the new avatar
        await self.user.edit(avatar=data)

    async def get_avatar(self) -> Optional[Asset]:
        # Throw exception if the bot isn't logged in
        if not self.user:
            raise NotLoggedIn

        # Get the bot user and get its avatar
        user: User = await self.fetch_user(self.user.id)
        return user.avatar

    async def set_banner(self, new_banner: Optional[bytes | Attachment]):
        # Throw exception if the bot isn't logged in
        if not self.user:
            raise NotLoggedIn

        # Read the attachment if necessary or just store the byte array
        data: Optional[bytes] = None
        if isinstance(new_banner, Attachment):
            data = await new_banner.read()
        else:
            data = new_banner

        # Set the new banner
        await self.user.edit(banner=data)

    async def get_banner(self) -> Optional[Asset]:
        # Throw exception if the bot isn't logged in
        if not self.user:
            raise NotLoggedIn

        # Get the bot user and get its banner
        user: User = await self.fetch_user(self.user.id)
        return user.banner

    # @overrides Bot
    async def setup_hook(self):
        # Configure extensions.
        if self._extensions_data:
            await self._configure_extensions(self._extensions_data)
        else:
            self.log.warning("No extensions configured.")

        # Sync global app commands and build the command cache.
        # We only build the guild command cache since `sync()` will build the global command cache.
        if self._sync_tree_on_login:
            await self.command_tree.sync()
            await self.command_tree.build_guild_cache(self.guilds)
        # Otherwise, just build the command cache.
        else:
            await self.command_tree.build_global_cache()
            await self.command_tree.build_guild_cache(self.guilds)

    # @overrides Bot
    async def on_connect(self):
        self.log.warning("Connected to Discord.")
        self._connected_since = utcnow()

    # @overrides Bot
    async def on_disconnect(self):
        self.log.warning("Disconnected from Discord.")

    # @overrides Bot
    async def on_error(self, event_method: str, *args: Any, **kwargs: Any):
        _, ex, _ = sys.exc_info()
        if isinstance(ex, Exception):
            event_data = EventData(event_method, args, kwargs)
            await self.error_handling.on_event_error(ex, event_data)
        else:
            await super().on_error(event_method, *args, **kwargs)

    # @overrides Bot
    async def on_command_error(self, ctx: Context, ex: Exception):
        await self.error_handling.on_command_error(ex, ctx)

    # Callback for `CommandTree.on_error()`
    async def on_app_command_error(self, interaction: Interaction, ex: Exception):
        await self.error_handling.on_app_command_error(ex, interaction)
