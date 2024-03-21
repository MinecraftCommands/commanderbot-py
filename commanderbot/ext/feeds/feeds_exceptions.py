from commanderbot.lib import ChannelID, ResponsiveException


class FeedsException(ResponsiveException):
    pass


class SubscriptionAlreadyExists(FeedsException):
    def __init__(self, channel_id: ChannelID):
        super().__init__(f"🤷 <#{channel_id}> is already subscribed to that feed")


class SubscriptionDoesNotExist(FeedsException):
    def __init__(self, channel_id: ChannelID):
        super().__init__(f"😬 <#{channel_id}> is not subscribed to that feed")


class ChannelHasNoSubscriptions(FeedsException):
    def __init__(self, channel_id: ChannelID):
        super().__init__(f"😔 <#{channel_id}> is not subscribed to any feeds")
