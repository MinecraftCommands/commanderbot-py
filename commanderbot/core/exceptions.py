from discord.ext.commands import ExtensionError


class CommanderBotException(Exception):
    pass


class ExtensionNotInConfig(CommanderBotException, ExtensionError):
    def __init__(self, name: str) -> None:
        super().__init__(f"Extension {name!r} is not in the config.", name=name)


class NotLoggedIn(CommanderBotException):
    def __init__(self):
        super().__init__("The bot isn't logged in!")
