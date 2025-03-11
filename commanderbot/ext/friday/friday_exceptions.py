from commanderbot.lib import ChannelID, ResponsiveException


class FridayException(ResponsiveException):
    pass


class RuleAlreadyExists(FridayException):
    def __init__(self, name: str):
        self.name: str = name
        super().__init__(f"😬 A rule called `{self.name}` already exists")


class RuleDoesNotExist(FridayException):
    def __init__(self, name: str):
        self.name: str = name
        super().__init__(f"😬 A rule called `{self.name}` does not exist")


class ChannelAlreadyRegistered(FridayException):
    def __init__(self, channel_id: ChannelID):
        self.channel_id: ChannelID = channel_id
        super().__init__(f"😬 <#{self.channel_id}> is already registered")


class ChannelNotRegistered(FridayException):
    def __init__(self, channel_id: ChannelID):
        self.channel_id: ChannelID = channel_id
        super().__init__(f"😬 <#{self.channel_id}> is not registered")


class InvalidRuleChance(FridayException):
    def __init__(self, chance: str):
        self.chance: str = chance
        super().__init__(f"😬 `{self.chance}` is not a valid chance for a rule")


class InvalidRuleCooldown(FridayException):
    def __init__(self, cooldown: str):
        self.cooldown: str = cooldown
        super().__init__(f"😬 `{self.cooldown}` is not a valid cooldown for a rule")
