from commanderbot.lib import ResponsiveException


class McdocException(ResponsiveException):
    pass


class RequestError(McdocException):
    def __init__(self):
        super().__init__(f"😵 Unable to fetch vanilla-mcdoc symbol data")


class QueryReturnedNoResults(McdocException):
    def __init__(self, query: str):
        self.query: str = query
        super().__init__(f"😔 Could not find any symbols matching `{self.query}`")
