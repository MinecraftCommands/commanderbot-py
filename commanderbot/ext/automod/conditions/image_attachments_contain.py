import asyncio
import unicodedata
from itertools import chain
from typing import Any, Literal, Optional, override

from pydantic import Field, PositiveInt

from commanderbot.core.utils import is_commander_bot
from commanderbot.ext.automod.automod_context import AutomodContext
from commanderbot.ext.automod.automod_exceptions import OCRNotSupported
from commanderbot.ext.automod.condition import AutomodCondition
from commanderbot.ext.automod.types import ContextAttachment
from commanderbot.lib.constants import SUPPORTS_OCR
from commanderbot.lib.types import (
    TesseractLanguages,
    TesseractScripts,
    UnicodeNormalizationForms,
)

__all__ = ("ImageAttachmentsContain",)

if SUPPORTS_OCR:
    from commanderbot.ext.automod.conditions.ocr_utils.pipeline import get_text


class ImageAttachmentsContain(AutomodCondition):
    """
    OCR image attachments and check if they contain a number of substrings.
    """

    type: Literal["image_attachments_contain"]

    languages: set[TesseractLanguages] = Field(default_factory=lambda: {"eng"})
    """
    The languages to recognize. If not set, `eng` will be recognized by default.
    """

    scripts: set[TesseractScripts] = Field(default_factory=set)
    """
    The scripts to recognize.
    """

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

    timeout: PositiveInt = 10
    """The max amount of time in seconds to wait for OCR results."""

    @override
    def model_post_init(self, context: Any):
        if self.ignore_case:
            self.contains = {s.lower() for s in self.contains}

    def _check_ocr_result(self, content: str) -> bool:
        # Process image content
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

        return False

    async def _ocr(
        self, context: AutomodContext, attachments: list[ContextAttachment]
    ) -> Optional[ContextAttachment]:
        # Create `lang` scring from languages and scripts
        lang: str = "+".join((v for v in chain(self.languages, self.scripts)))

        # Submit OCR tasks to the process pool
        assert is_commander_bot(context.bot)
        pool = context.bot.pool
        loop = asyncio.get_running_loop()
        tasks = [
            loop.run_in_executor(pool, get_text, data, lang, idx)
            for idx, (_, data, _) in enumerate(attachments)
        ]

        # Check OCR results as they come in
        try:
            for task in asyncio.as_completed(tasks, timeout=self.timeout):
                if result := await task:
                    text, idx = result
                    # Check if the text passes the condition and return the attachment
                    if self._check_ocr_result(text):
                        return attachments[idx]
        finally:
            for task in tasks:
                if not task.done():
                    task.cancel()

    @override
    async def check(self, context: AutomodContext) -> bool:
        # Throw an exception if OCR isn't supported
        if not SUPPORTS_OCR:
            raise OCRNotSupported

        # We need image attachments in context
        attachments = await context.fetch_attachments_with_type("image")
        if not attachments:
            return False

        # OCR image attachments
        if attachment := await self._ocr(context, attachments):
            # Add attachment to metadata
            passed_ocr = context.get_metadata("passed_ocr_condition") or []
            passed_ocr.append(attachment)
            context.set_metadata("passed_ocr_condition", passed_ocr)
            return True

        # If we got this far, none of the attachments passed the condition
        return False
