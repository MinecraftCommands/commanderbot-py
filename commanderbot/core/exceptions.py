class ConfigException(Exception):
    pass


class ExtensionNotInConfig(ConfigException):
    def __init__(self, name: str):
        super().__init__(f"Extension {name} is not in the config.")


class ExtensionIsRequired(ConfigException):
    def __init__(self, name: str):
        super().__init__(f"Extension {name} is a required extension.")


class CommanderBotException(Exception):
    pass


class NotLoggedIn(CommanderBotException):
    def __init__(self):
        super().__init__("The bot isn't logged in!")
