from commanderbot.lib.types import EmojiID


class ConfigException(Exception):
    pass


class ExtensionNotInConfig(ConfigException):
    def __init__(self, name: str):
        super().__init__(f"Extension {name} is not in the config.")


class ExtensionIsRequired(ConfigException):
    def __init__(self, name: str):
        super().__init__(f"Extension {name} is a required extension.")


class ApplicationEmojiManagerException(Exception):
    pass


class ApplicationEmojiDoesNotExist(ApplicationEmojiManagerException):
    def __init__(self, emoji: str | EmojiID):
        super().__init__(f"Application emoji {emoji} does not exist.")


class CommanderBotException(Exception):
    pass


class NotLoggedIn(CommanderBotException):
    def __init__(self):
        super().__init__("The bot isn't logged in!")
