from commanderbot.lib import ResponsiveException


class MCCQException(ResponsiveException):
    pass


class JavaQueryManagerNotConfigured(MCCQException):
    def __init__(self):
        super().__init__("😔 MCCQ has not been configured for Minecraft: Java Edition")


class BedrockQueryManagerNotConfigured(MCCQException):
    def __init__(self):
        super().__init__(
            "😔 MCCQ has not been configured for Minecraft: Bedrock Edition"
        )


class InvalidArguments(MCCQException):
    def __init__(self):
        super().__init__("😬 Invalid arguments for that command")


class NoVersionsAvailable(MCCQException):
    def __init__(self):
        super().__init__("😵 No versions available for that command")


class FailedToLoadData(MCCQException):
    def __init__(self):
        super().__init__("😵 Failed to load data for that command")


class InvalidRegex(MCCQException):
    def __init__(self):
        super().__init__(
            "😬 Invalid regex for that command (you may need to use escaping)"
        )


class QueryReturnedNoResults(MCCQException):
    def __init__(self):
        super().__init__("😔 No results found for that command")
