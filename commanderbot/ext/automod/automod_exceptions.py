from commanderbot.lib.exceptions import ResponsiveException


class AutomodException(ResponsiveException):
    pass


class CouldNotValidateNewAutomodRule(AutomodException):
    def __init__(self, exception: ValueError):
        self.exception = exception
        super().__init__(
            f"😵 An error occurred while validating the new automod rule:\n```\n{exception}\n```"
        )


class CouldNotValidateModifiedAutomodRule(AutomodException):
    def __init__(self, exception: ValueError):
        self.exception = exception
        super().__init__(
            f"😵 An error occurred while validating the modified automod rule:\n```\n{exception}\n```"
        )


class CouldNotValidateUploadedAutomodRule(AutomodException):
    def __init__(self, exception: ValueError):
        self.exception = exception
        super().__init__(
            f"😵 An error occurred while validating the uploaded automod rule:\n```\n{exception}\n```"
        )


class UploadIsNotJsonFile(AutomodException):
    def __init__(self):
        super().__init__("🤔 The uploaded automod rule is not a Json file")


class DefaultLogChannelNotConfigured(AutomodException):
    def __init__(self):
        super().__init__("🤔 The default log channel has not been configured")


class AutomodRuleAlreadyExists(AutomodException):
    def __init__(self, name: str):
        self.name: str = name
        super().__init__(f"🤷 Automod rule `{self.name}` already exists")


class AutomodRuleDoesNotExist(AutomodException):
    def __init__(self, name: str):
        self.name: str = name
        super().__init__(f"😬 Automod rule `{self.name}` does not exist")


class AutomodRuleAlreadyEnabled(AutomodException):
    def __init__(self, name: str):
        self.name: str = name
        super().__init__(f"😬 Automod rule `{name}` is already enabled")


class AutomodRuleAlreadyDisabled(AutomodException):
    def __init__(self, name: str):
        self.name: str = name
        super().__init__(f"😬 Automod rule `{name}` is already disabled")


class AutomodRuleMetadataAlreadyExists(AutomodException):
    def __init__(self, name: str):
        self.name: str = name
        super().__init__(
            f"😬 Automod rule metadata `{self.name}` already exists (This should never happen!!!)"
        )


class AutomodRuleMetadataDoesNotExist(AutomodException):
    def __init__(self, name: str):
        self.name: str = name
        super().__init__(
            f"🤷 Automod rule metadata `{self.name}` does not exist (This should never happen!!!)"
        )


class AutomodBucketAlreadyExists(AutomodException):
    def __init__(self, name: str):
        self.name: str = name
        super().__init__(f"🤷 Automod bucket `{self.name}` already exists")


class AutomodBucketDoesNotExist(AutomodException):
    def __init__(self, name: str):
        self.name: str = name
        super().__init__(f"😬 Automod bucket `{self.name}` does not exist")


class AutomodBucketAlreadyEnabled(AutomodException):
    def __init__(self, name: str):
        self.name: str = name
        super().__init__(f"😬 Automod bucket `{name}` is already enabled")


class AutomodBucketAlreadyDisabled(AutomodException):
    def __init__(self, name: str):
        self.name: str = name
        super().__init__(f"😬 Automod bucket `{name}` is already disabled")


class OCRNotSupported(AutomodException):
    def __init__(self):
        super().__init__(
            "Automod does not support OCR. The feature is either not installed or misconfigured"
        )


class AutomodValidationError(ValueError):
    pass
