from discord.app_commands import AppCommandError

from commanderbot.lib import ResponsiveException


class ManifestException(ResponsiveException):
    pass


class ManifestTransformerException(ResponsiveException, AppCommandError):
    pass


class NoURLInConfig(ManifestException):
    def __init__(self):
        super().__init__(
            "❌ Unable to update the latest min engine version since no URL was given in the bot config"
        )


class BadResponseFromVersionURL(ManifestException):
    def __init__(self, status_code: int):
        self.status_code: int = status_code
        super().__init__(
            f"❌ Unable to update the latest min engine version (Status code: `{status_code}`)"
        )


class UnableToUpdateLatestVersion(ManifestException):
    def __init__(self):
        super().__init__("❌ Unable to update the latest min engine version")


class InvalidVersionFormat(ManifestTransformerException):
    def __init__(self):
        super().__init__("😬 Versions must use the `<major>.<minor>.<patch>` format")
