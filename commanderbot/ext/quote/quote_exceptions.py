from commanderbot.lib import ResponsiveException


class QuoteException(ResponsiveException):
    pass


class ChannelNotMessageable(QuoteException):
    def __init__(self):
        super().__init__("😳 I can't quote that")


class MissingQuotePermissions(QuoteException):
    def __init__(self):
        super().__init__("😠 You can't quote that")
