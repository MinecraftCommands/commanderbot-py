from typing import Any

from discord import Object
from discord.ext.commands import Cog

from commanderbot.lib.responsive_exception import ResponsiveException


class SudoException(ResponsiveException):
    pass


class GlobalSyncError(SudoException):
    def __init__(self, reason: str):
        super().__init__(
            f"😵 **Unable to sync app commands globally**\n> Reason: `{reason}`"
        )


class GuildSyncError(SudoException):
    def __init__(self, guild: Object, reason: str):
        super().__init__(
            "😵 **Unable to sync app commands to this guild**\n"
            f"> Guild ID: `{guild.id}`\n"
            f"> Reason: `{reason}`"
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
