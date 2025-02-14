from typing import Any

from discord import Object
from discord.app_commands import AppCommandError
from discord.ext.commands import Cog

from commanderbot.lib import ResponsiveException


class SudoTransformerException(ResponsiveException, AppCommandError):
    pass


class ExtensionResolutionError(SudoTransformerException):
    def __init__(self, reason: str):
        self.reason: str = reason.replace("\n", " ")
        super().__init__(
            f"😔 Unable to resolve that extension:\n```\n{self.reason}\n```"
        )


class CannotManageExtensionNotInConfig(SudoTransformerException):
    def __init__(self, name: str):
        super().__init__(
            f"😬 Extension `{name}` is not in the config and cannot be managed"
        )


class CannotManageRequiredExtension(SudoTransformerException):
    def __init__(self, name: str):
        super().__init__(f"😬 Extension `{name}` is required and cannot be managed")


class CannotFindApplicationEmoji(SudoTransformerException):
    def __init__(self, name: str):
        super().__init__(f"😬 Application emoji `{name}` does not exist")


class SudoException(ResponsiveException):
    pass


class ExtensionLoadError(SudoException):
    def __init__(self, name: str, reason: str):
        self.reason: str = reason.replace("\n", " ")
        super().__init__(
            f"😵 Unable to load extension `{name}`:\n```\n{self.reason}\n```"
        )


class ExtensionUnloadError(SudoException):
    def __init__(self, name: str, reason: str):
        self.reason: str = reason.replace("\n", " ")
        super().__init__(
            f"😵 Unable to unload extension `{name}`:\n```\n{self.reason}\n```"
        )


class ExtensionReloadError(SudoException):
    def __init__(self, name: str, reason: str):
        self.reason: str = reason.replace("\n", " ")
        super().__init__(
            f"😵 Unable to reload extension `{name}`:\n```\n{self.reason}\n```"
        )


class GlobalSyncError(SudoException):
    def __init__(self, reason: str):
        self.reason: str = reason.replace("\n", " ")
        super().__init__(
            f"😵 Unable to sync app commands globally:\n```\n{self.reason}\n```"
        )


class GuildSyncError(SudoException):
    def __init__(self, guild: Object, reason: str):
        self.reason: str = reason.replace("\n", " ")
        super().__init__(
            f"😵 Unable to sync app commands to this guild (`{guild.id}`):\n```\n{self.reason}\n```"
        )


class GuildIDNotFound(SudoException):
    def __init__(self):
        super().__init__(
            "😬 A guild ID was not provided or a guild ID could not be found in the current context"
        )


class UnknownCog(SudoException):
    def __init__(self, cog: str):
        super().__init__(f"😔 Unable to find a loaded cog with the name `{cog}`")


class CogHasNoStore(SudoException):
    def __init__(self, cog: Cog):
        super().__init__(f"😬 The cog `{cog.qualified_name}` does not use a store")


class UnsupportedStoreExport(SudoException):
    def __init__(self, store: Any):
        super().__init__(f"😬 Unsupported store export: `{type(store)}`")


class BotHasNoAvatar(SudoException):
    def __init__(self):
        super().__init__("😵 The bot doesn't have an avatar set")


class BotHasNoBanner(SudoException):
    def __init__(self):
        super().__init__("😵 The bot doesn't have a banner set")


class ErrorChangingBotAvatar(SudoException):
    def __init__(self, reason: str):
        self.reason: str = reason.replace("\n", " ")
        super().__init__(
            f"😬 An error occurred while changing the bot's avatar:\n```\n{self.reason}\n```"
        )


class ErrorChangingBotBanner(SudoException):
    def __init__(self, reason: str):
        self.reason: str = reason.replace("\n", " ")
        super().__init__(
            f"😬 An error occurred while changing the bot's banner:\n```\n{self.reason}\n```"
        )


class ErrorAddingApplicationEmoji(SudoException):
    def __init__(self, reason: str):
        self.reason: str = reason.replace("\n", " ")
        super().__init__(
            f"😬 An error occurred while adding an application emoji:\n```\n{self.reason}\n```"
        )

class ErrorRenamingApplicationEmoji(SudoException):
    def __init__(self, reason: str):
        self.reason: str = reason.replace("\n", " ")
        super().__init__(
            f"😬 An error occurred while renaming an application emoji:\n```\n{self.reason}\n```"
        )

class ErrorRemovingApplicationEmoji(SudoException):
    def __init__(self, reason: str):
        self.reason: str = reason.replace("\n", " ")
        super().__init__(
            f"😬 An error occurred while removing an application emoji:\n```\n{self.reason}\n```"
        )
