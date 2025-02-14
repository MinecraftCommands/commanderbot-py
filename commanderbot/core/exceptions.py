from commanderbot.lib.types import EmojiID


class ConfigException(Exception):
    pass


class ExtensionNotInConfig(ConfigException):
    def __init__(self, extension_name: str):
        self.extension_name: str = extension_name
        super().__init__(f"Extension {self.extension_name} is not in the config.")


class ExtensionIsRequired(ConfigException):
    def __init__(self, extension_name: str):
        self.extension_name: str = extension_name
        super().__init__(f"Extension {self.extension_name} is a required extension.")


class ApplicationEmojiManagerException(Exception):
    pass


class ApplicationEmojiDoesNotExist(ApplicationEmojiManagerException):
    def __init__(self, emoji: str | EmojiID):
        self.emoji: str | EmojiID = emoji
        super().__init__(f"Application emoji {self.emoji} does not exist.")


class CommanderBotException(Exception):
    pass


class NotLoggedIn(CommanderBotException):
    def __init__(self):
        super().__init__("The bot isn't logged in!")
