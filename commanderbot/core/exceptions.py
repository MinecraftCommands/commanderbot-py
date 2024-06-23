class CommanderBotException(Exception):
    pass


class NotLoggedIn(CommanderBotException):
    def __init__(self):
        super().__init__("The bot isn't logged in")
