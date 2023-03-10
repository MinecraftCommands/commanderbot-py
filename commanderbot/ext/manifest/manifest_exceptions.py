from discord.app_commands import AppCommandError

from commanderbot.lib import ResponsiveException


class ManifestTransformerException(ResponsiveException, AppCommandError):
    pass


class InvalidVersionFormat(ManifestTransformerException):
    def __init__(self):
        super().__init__("😬 Versions must use the `<major>.<minor>.<patch>` format")
