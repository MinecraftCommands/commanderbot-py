from commanderbot.lib import ResponsiveException


class McdocException(ResponsiveException):
    pass


class RequestSymbolsError(McdocException):
    def __init__(self):
        super().__init__(f"😵 Unable to fetch vanilla-mcdoc symbol data")


class RequestVersionError(McdocException):
    def __init__(self):
        super().__init__(f"😵 Unable to fetch the latest version number")


class InvalidVersionError(McdocException):
    def __init__(self, version: str):
        self.version: str = version
        super().__init__(f"😬 Invalid version format `{self.version}`. Only release versions are allowed.")


class QueryReturnedNoResults(McdocException):
    def __init__(self, query: str):
        self.query: str = query
        super().__init__(f"😔 Could not find any symbols matching `{self.query}`")
