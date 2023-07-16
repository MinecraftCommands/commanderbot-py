from commanderbot.lib import ResponsiveException


class FaqException(ResponsiveException):
    pass


class FaqKeyAlreadyExists(FaqException):
    def __init__(self, key: str):
        self.key: str = key
        super().__init__(f"🤷 FAQ key `{self.key}` already exists")


class FaqKeyMatchesExistingAlias(FaqException):
    def __init__(self, key: str):
        self.key: str = key
        super().__init__(f"🤷 FAQ key `{self.key}` matches an existing FAQ alias")


class FaqKeyMatchesOwnAlias(FaqException):
    def __init__(self):
        super().__init__("🤷 A FAQ's aliases can't contain the key")


class FaqAliasAlreadyExists(FaqException):
    def __init__(self, alias: str):
        self.alias: str = alias
        super().__init__(f"🤷 FAQ alias `{self.alias}` already exists")


class FaqAliasMatchesExistingKey(FaqException):
    def __init__(self, alias: str):
        self.alias: str = alias
        super().__init__(f"🤷 FAQ alias `{self.alias}` matches an existing FAQ key")


class FaqDoesNotExist(FaqException):
    def __init__(self, key: str):
        self.key: str = key
        super().__init__(f"😬 FAQ `{self.key}` does not exist")


class QueryReturnedNoResults(FaqException):
    def __init__(self, query: str, *suggestions: str):
        self.query: str = query
        self.suggestions = ", ".join((f"`{key}`" for key in suggestions))
        super().__init__(
            f"🤔 Could not find any FAQs matching `{self.query}`, but maybe you meant: {self.suggestions}"
            if self.suggestions
            else f"😔 Could not find any FAQs matching `{self.query}`"
        )


class InvalidPrefixPattern(FaqException):
    def __init__(self, prefix: str, reason: str):
        self.prefix: str = prefix
        self.reason: str = reason
        super().__init__(
            f"😬 Invalid FAQ prefix pattern\n> **Pattern**: `{self.prefix}`\n> **Reason**: {self.reason}"
        )


class InvalidMatchPattern(FaqException):
    def __init__(self, match: str, reason: str):
        self.match: str = match
        self.reason: str = reason
        super().__init__(
            f"😬 Invalid FAQ match pattern\n> **Pattern**: `{self.match}`\n> **Reason**: {self.reason}"
        )


class PrefixPatternNotSet(FaqException):
    def __init__(self):
        super().__init__("😬 A FAQ prefix pattern has not been set")


class MatchPatternNotSet(FaqException):
    def __init__(self):
        super().__init__("😬 A FAQ match pattern has not been set")
