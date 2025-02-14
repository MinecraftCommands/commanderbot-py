from typing import Any

from discord import Object
from discord.app_commands import AppCommandError

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
    def __init__(self, extension_name: str):
        self.extension_name: str = extension_name
        super().__init__(
            f"😬 Extension `{self.extension_name}` is not in the config and cannot be managed"
        )


class CannotManageRequiredExtension(SudoTransformerException):
    def __init__(self, extension_name: str):
        self.extension_name: str = extension_name
        super().__init__(f"😬 Extension `{self.extension_name}` is required and cannot be managed")


class CannotFindApplicationEmoji(SudoTransformerException):
    def __init__(self, emoji_name: str):
        self.emoji_name: str = emoji_name
        super().__init__(f"😬 Application emoji `{self.emoji_name}` does not exist")


class SudoException(ResponsiveException):
    pass


class ExtensionLoadError(SudoException):
    def __init__(self, extension_name: str, reason: str):
        self.extension_name: str = extension_name
        self.reason: str = reason.replace("\n", " ")
        super().__init__(
            f"😵 Unable to load extension `{self.extension_name}`:\n```\n{self.reason}\n```"
        )


class ExtensionUnloadError(SudoException):
    def __init__(self, extension_name: str, reason: str):
        self.extension_name: str = extension_name
        self.reason: str = reason.replace("\n", " ")
        super().__init__(
            f"😵 Unable to unload extension `{self.extension_name}`:\n```\n{self.reason}\n```"
        )


class ExtensionReloadError(SudoException):
    def __init__(self, extension_name: str, reason: str):
        self.extension_name: str = extension_name
        self.reason: str = reason.replace("\n", " ")
        super().__init__(
            f"😵 Unable to reload extension `{self.extension_name}`:\n```\n{self.reason}\n```"
        )


class GlobalSyncError(SudoException):
    def __init__(self, reason: str):
        self.reason: str = reason.replace("\n", " ")
        super().__init__(
            f"😵 Unable to sync app commands globally:\n```\n{self.reason}\n```"
        )


class GuildSyncError(SudoException):
    def __init__(self, guild: Object, reason: str):
        self.guild: Object = guild
        self.reason: str = reason.replace("\n", " ")
        super().__init__(
            f"😵 Unable to sync app commands to this guild (`{self.guild.id}`):\n```\n{self.reason}\n```"
        )


class GuildIDNotFound(SudoException):
    def __init__(self):
        super().__init__(
            "😬 A guild ID was not provided or a guild ID could not be found in the current context"
        )


class UnknownCog(SudoException):
    def __init__(self, cog_name: str):
        self.cog_name: str = cog_name
        super().__init__(f"😔 Unable to find a loaded cog with the name `{self.cog_name}`")


class CogHasNoStore(SudoException):
    def __init__(self, cog_name: str):
        self.cog_name: str = cog_name
        super().__init__(f"😬 The cog `{self.cog_name}` does not use a store")


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
            f"😬 Unable to change the bot's avatar:\n```\n{self.reason}\n```"
        )


class ErrorChangingBotBanner(SudoException):
    def __init__(self, reason: str):
        self.reason: str = reason.replace("\n", " ")
        super().__init__(
            f"😬 Unable to change the bot's banner:\n```\n{self.reason}\n```"
        )


class ErrorAddingApplicationEmoji(SudoException):
    def __init__(self, reason: str):
        self.reason: str = reason.replace("\n", " ")
        super().__init__(
            f"😬 Unable to add application emoji\n```\n{self.reason}\n```"
        )

class ErrorRenamingApplicationEmoji(SudoException):
    def __init__(self, reason: str):
        self.reason: str = reason.replace("\n", " ")
        super().__init__(
            f"😬 Unable to rename application emoji:\n```\n{self.reason}\n```"
        )

class ErrorRemovingApplicationEmoji(SudoException):
    def __init__(self, reason: str):
        self.reason: str = reason.replace("\n", " ")
        super().__init__(
            f"😬 Unable to remove application emoji:\n```\n{self.reason}\n```"
        )
