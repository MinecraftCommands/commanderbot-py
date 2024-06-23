from typing import Any

from discord import Object
from discord.ext.commands import Cog

from commanderbot.lib import ResponsiveException


class SudoException(ResponsiveException):
    pass


class GlobalSyncError(SudoException):
    def __init__(self, reason: str):
        self.reason: str = reason.replace("\n", " ")
        super().__init__(
            f"😵 **Unable to sync app commands globally**\n> Reason: `{self.reason}`"
        )


class GuildSyncError(SudoException):
    def __init__(self, guild: Object, reason: str):
        self.reason: str = reason.replace("\n", " ")
        super().__init__(
            "😵 **Unable to sync app commands to this guild**\n"
            f"> Guild ID: `{guild.id}`\n"
            f"> Reason: `{self.reason}`"
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
            f"😬 **An error ocurred while changing the bot's avatar**\n> Reason: `{self.reason}`"
        )


class ErrorChangingBotBanner(SudoException):
    def __init__(self, reason: str):
        self.reason: str = reason.replace("\n", " ")
        super().__init__(
            f"😬 **An error ocurred while changing the bot's banner**\n> Reason: `{self.reason}`"
        )
