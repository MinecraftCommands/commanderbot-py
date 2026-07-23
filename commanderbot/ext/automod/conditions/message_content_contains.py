import unicodedata
from typing import Any, Literal, Optional, override

from pydantic import Field, PositiveInt

from commanderbot.ext.automod.automod_context import AutomodContext
from commanderbot.ext.automod.condition import AutomodCondition
from commanderbot.lib.types import UnicodeNormalizationForms

__all__ = ("MessageContentContains",)


class MessageContentContains(AutomodCondition):
    """
    Check if the message content contains a number of substrings.
    """

    type: Literal["message_content_contains"]

    contains: set[str] = Field(min_length=1)
    """
    The substrings to find. Unless `count` is specified, all substrings must be
    found in order to pass.
    """

    count: Optional[PositiveInt] = None
    """
    The number of unique substrings to find. For example: a value of 1 requires any
    of the substrings to be found, whereas a value of 2 requires at least 2 to be
    found. If empty, all substrings must be found.
    """

    ignore_case: bool = False
    """Whether to ignore upper vs lower case."""

    use_normalization: bool = False
    """Whether to use unicode normalization or process the string as-is."""

    normalization_form: UnicodeNormalizationForms = Field(default="NFKD")
    """If enabled, the type of normalization to apply. Defaults to NFKD."""

    @override
    def model_post_init(self, context: Any):
        if self.ignore_case:
            self.contains = {s.lower() for s in self.contains}

    @override
    async def check(self, context: AutomodContext) -> bool:
        # Return if the event has no message
        message = context.event.message
        if not message:
            return False

        # Grab the message content and process it
        content = message.content
        if self.use_normalization:
            content = unicodedata.normalize(self.normalization_form, content)
        if self.ignore_case:
            content = content.lower()

        # Check for a sufficient number of substrings
        required_matches = self.count or len(self.contains)
        matches = 0
        for substring in self.contains:
            if substring in content:
                matches += 1
                if matches == required_matches:
                    return True

        # If we got this far, we didn't have enough substring matches
        return False
