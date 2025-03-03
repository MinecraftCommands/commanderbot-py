from commanderbot.lib import ResponsiveException


class FridayException(ResponsiveException):
    pass


class RuleAlreadyExists(FridayException):
    def __init__(self, name: str):
        super().__init__(f"😬 A rule called `{name}` already exists")


class RuleDoesNotExist(FridayException):
    def __init__(self, name: str):
        super().__init__(f"😬 A rule called `{name}` does not exist")
