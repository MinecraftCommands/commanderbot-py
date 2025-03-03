from commanderbot.lib import ChannelID, ResponsiveException


class FridayException(ResponsiveException):
    pass


class RuleAlreadyExists(FridayException):
    def __init__(self, name: str):
        super().__init__(f"😬 A rule called `{name}` already exists")


class RuleDoesNotExist(FridayException):
    def __init__(self, name: str):
        super().__init__(f"😬 A rule called `{name}` does not exist")


class ChannelAlreadyRegistered(FridayException):
    def __init__(self, channel_id: ChannelID):
        super().__init__(f"😬 <#{channel_id}> is already registered")


class ChannelNotRegistered(FridayException):
    def __init__(self, channel_id: ChannelID):
        super().__init__(f"😬 <#{channel_id}> is not registered")
