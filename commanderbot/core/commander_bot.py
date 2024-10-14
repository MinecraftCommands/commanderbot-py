import importlib.util
import sys
from datetime import datetime, timedelta
from logging import Logger, getLogger
from typing import Any, Optional, Type

from discord import AppInfo, Asset, Attachment, User
from discord.ext.commands import Bot, Cog, Context, ExtensionNotFound
from discord.interactions import Interaction
from discord.utils import utcnow

from commanderbot.core.command_tree import CachingCommandTree
from commanderbot.core.config import Config
from commanderbot.core.configured_extension import ConfiguredExtension
from commanderbot.core.error_handling import (
    AppCommandErrorHandler,
    CommandErrorHandler,
    ErrorHandling,
    EventErrorHandler,
)
from commanderbot.core.exceptions import NotLoggedIn
from commanderbot.core.help_command import HelpCommand
from commanderbot.lib import EventData


class CommanderBot(Bot):
    def __init__(self, config: Config, sync_tree_on_login: bool = False):
        # Store the config and if the command tree should sync on login
        self.config: Config = config
        self._sync_tree_on_login: bool = sync_tree_on_login

        # Initialize discord.py Bot base.
        super().__init__(
            command_prefix=config.command_prefix,
            intents=config.intents,
            allowed_mentions=config.allowed_mentions,
            help_command=HelpCommand(),
            tree_cls=CachingCommandTree,
        )

        # Grab our own logger instance.
        self.log: Logger = getLogger("CommanderBot")

        # Remember when we started and the last time we connected.
        self._started_at: datetime = utcnow()
        self._connected_since: Optional[datetime] = None

        # Create an error handling component.
        self.error_handling = ErrorHandling(log=self.log)
        self.tree.on_error = self.on_app_command_error

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

    def add_event_error_handler(self, handler: EventErrorHandler):
        self.error_handling.add_event_error_handler(handler)

    def add_command_error_handler(self, handler: CommandErrorHandler):
        self.error_handling.add_command_error_handler(handler)

    def add_app_command_error_handler(self, handler: AppCommandErrorHandler):
        self.error_handling.add_app_command_error_handler(handler)

    async def add_configured_cog(self, ext_name: str, cog_class: Type[Cog]):
        cog: Optional[Cog] = None
        if options := self.config.get_extension_options(ext_name):
            cog = cog_class(self, **options)
        else:
            cog = cog_class(self)

        await self.add_cog(cog)

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

    async def set_description(self, new_description: Optional[str]):
        app: AppInfo = await self.application_info()
        await app.edit(description=new_description)

    async def get_description(self) -> Optional[str]:
        app: AppInfo = await self.application_info()
        return app.description or None

    def _resolve_extension_name(self, name: str, package: Optional[str]) -> str:
        try:
            return importlib.util.resolve_name(name, package)
        except ImportError:
            raise ExtensionNotFound(name)

    # @overrides Bot
    async def load_extension(self, name: str, *, package: Optional[str] = None):
        try:
            # Resolve the extension name and get the extension.
            resolved_name: str = self._resolve_extension_name(name, package)
            ext: ConfiguredExtension = self.config.require_extension(resolved_name)

            # Load extension and enable it in the config.
            self.log.info(f"[--->] {ext.name}")
            await super().load_extension(ext.name)
            self.config.enable_extension(ext.name)
        except Exception as ex:
            self.log.exception(f"Failed to load extension: {name}")
            raise ex

    # @overrides Bot
    async def unload_extension(self, name: str, *, package: Optional[str] = None):
        try:
            # Resolve the extension name and get the extension
            resolved_name: str = self._resolve_extension_name(name, package)
            ext: ConfiguredExtension = self.config.require_extension(resolved_name)

            # Unload extension and disable it in the config
            self.log.info(f"[-x->] {ext.name}")
            await super().unload_extension(name)
            self.config.disable_extension(name)
        except Exception as ex:
            self.log.exception(f"Failed to unload extension: {name}")
            raise ex

    # @overrides Bot
    async def reload_extension(self, name: str, *, package: Optional[str] = None):
        try:
            # Resolve the extension name and get the extension
            resolved_name: str = self._resolve_extension_name(name, package)
            ext: ConfiguredExtension = self.config.require_extension(resolved_name)

            # Reload extension
            self.log.info(f"[-o->] {ext.name}")
            await super().reload_extension(ext.name)
        except Exception as ex:
            self.log.exception(f"Failed to reload extension: {name}")
            raise ex

    # @overrides Bot
    async def setup_hook(self):
        # Load extensions
        self.log.info(
            f"Loading {len(self.config.enabled_extensions)} enabled extensions..."
        )

        for ext in self.config.enabled_extensions:
            await self.load_extension(ext.name)

        self.log.info(f"Finished loading extensions.")

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
