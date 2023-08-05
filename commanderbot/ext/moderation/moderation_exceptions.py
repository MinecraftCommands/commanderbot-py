from commanderbot.lib import ResponsiveException


class ModerationException(ResponsiveException):
    pass


class CannotKickBotOrSelf(ModerationException):
    def __init__(self):
        super().__init__("😳 I don't think you want to do that...")


class CannotKickElevatedUsers(ModerationException):
    def __init__(self):
        super().__init__("😠 You can't kick users with elevated permissions")


class CannotBanBotOrSelf(ModerationException):
    def __init__(self):
        super().__init__("😳 I don't think you want to do that...")


class CannotBanElevatedUsers(ModerationException):
    def __init__(self):
        super().__init__("😠 You can't ban users with elevated permissions")
