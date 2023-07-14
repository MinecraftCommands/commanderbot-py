from commanderbot.lib import ResponsiveException


class FaqException(ResponsiveException):
    pass


class FaqAlreadyExists(FaqException):
    def __init__(self, key: str):
        self.key: str = key
        super().__init__(f"🤷 FAQ `{self.key}` already exists")


class FaqAliasAlreadyExists(FaqException):
    def __init__(self, alias: str):
        self.alias: str = alias
        super().__init__(f"🤷 FAQ alias `{self.alias}` already exists")


class FaqDoesNotExist(FaqException):
    def __init__(self, key: str):
        self.key: str = key
        super().__init__(f"😬 FAQ `{self.key}` does not exist")


class QueryReturnedNoResults(FaqException):
    def __init__(self, query: str, *suggestions: str):
        self.query: str = query
        self.suggestions = ", ".join((f"`{key}`" for key in suggestions))

        msg: str = f"😔 Could not find any FAQs matching `{self.query}`"
        if self.suggestions:
            msg = f"🤔 Could not find any FAQs matching `{self.query}`, but maybe you meant: {self.suggestions}"

        super().__init__(msg)


class InvalidPrefixPattern(FaqException):
    def __init__(self, prefix: str, reason: str):
        self.prefix: str = prefix
        self.reason: str = reason
        super().__init__(
            f"😬 Invalid prefix pattern\n> **Pattern**: `{self.prefix}`\n> **Reason**: {self.reason}"
        )


class InvalidMatchPattern(FaqException):
    def __init__(self, match: str, reason: str):
        self.match: str = match
        self.reason: str = reason
        super().__init__(
            f"😬 Invalid match pattern\n> **Pattern**: `{self.match}`\n> **Reason**: {self.reason}"
        )


class PrefixPatternNotSet(FaqException):
    def __init__(self):
        super().__init__("😬 A prefix pattern has not been set")


class MatchPatternNotSet(FaqException):
    def __init__(self):
        super().__init__("😬 A match pattern has not been set")
