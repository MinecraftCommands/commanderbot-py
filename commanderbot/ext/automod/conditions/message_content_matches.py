import re
import unicodedata
from typing import Literal, Optional, override

from pydantic import Field, PositiveInt

from commanderbot.ext.automod.automod_context import AutomodContext
from commanderbot.ext.automod.condition import AutomodCondition
from commanderbot.lib.types import UnicodeNormalizationForms

__all__ = ("MessageContentMatches",)


class MessageContentMatches(AutomodCondition):
    """
    Check if the message content matches a number of regular expressions.
    """

    type: Literal["message_content_matches"]

    matches: set[re.Pattern] = Field(default_factory=set, min_length=1)
    """
    The patterns (regular expressions) to match. Unless `count` is specified, all
    patterns must be matched in order to pass.
    """

    count: Optional[PositiveInt] = None
    """
    The number of unique patterns to match. For example: a value of 1 requires any
    of the patterns to be matched, whereas a value of 2 requires at least 2 to be
    matched. If unspecified, all patterns must be matched.
    """

    use_search: bool = False
    """Whether to search the entire string instead of using an anchored match."""

    use_normalization: bool = False
    """Whether to use unicode normalization or process the string as-is."""

    normalization_form: UnicodeNormalizationForms = Field(default="NFKD")
    """If enabled, the type of normalization to apply. Defaults to NFKD."""

    def is_match(self, pattern: re.Pattern, content: str) -> bool:
        if self.use_search:
            return pattern.search(content) is not None
        return pattern.match(content) is not None

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

        # Check for a sufficient number of matches
        required_matches = self.count or len(self.matches)
        matches = 0
        for pattern in self.matches:
            if self.is_match(pattern, content):
                matches += 1
                if matches == required_matches:
                    return True

        # If we got this far, we didn't have enough matches
        return False
