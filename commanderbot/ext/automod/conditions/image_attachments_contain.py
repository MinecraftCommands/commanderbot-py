import asyncio
import unicodedata
from itertools import chain
from logging import Logger
from typing import Any, ClassVar, Literal, Optional, cast, override

import pebble
from pydantic import Field, PositiveFloat, PositiveInt

from commanderbot.core.utils import is_commander_bot
from commanderbot.ext.automod.automod_context import AutomodContext
from commanderbot.ext.automod.automod_exceptions import OCRNotSupported
from commanderbot.ext.automod.condition import AutomodCondition
from commanderbot.ext.automod.constants import IMAGE_MIME_TYPES
from commanderbot.lib.constants import SUPPORTS_OCR
from commanderbot.lib.types import (
    AttachmentID,
    TesseractLanguages,
    TesseractScripts,
    UnicodeNormalizationForms,
)

__all__ = ("ImageAttachmentsContain",)

if SUPPORTS_OCR:
    from commanderbot.ext.automod.conditions.ocr_utils.pipeline import get_text

MAX_OCR_WORKERS: int = 4


class ImageAttachmentsContain(AutomodCondition):
    """
    OCR image attachments in context and check if they contain a number of substrings.
    """

    type: Literal["image_attachments_contain"]

    languages: set[TesseractLanguages] = Field(
        default_factory=lambda: cast(set[TesseractLanguages], {"eng"})
    )
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

    timeout: PositiveFloat = 10
    """The max amount of time in seconds to wait for OCR results."""

    _semaphore: ClassVar[Optional[asyncio.Semaphore]] = None
    """Used to limit how many OCR workers get sumbitted to the pool."""

    @classmethod
    def get_semaphore(cls) -> asyncio.Semaphore:
        if cls._semaphore is None:
            cls._semaphore = asyncio.Semaphore(MAX_OCR_WORKERS)
        return cls._semaphore

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

    async def _ocr_worker(
        self,
        pool: pebble.ProcessPool,
        log: Logger,
        attachment_id: AttachmentID,
        data: bytes,
        lang: str,
    ) -> Optional[tuple[str, AttachmentID]]:
        future: Optional[pebble.ProcessFuture] = None
        try:
            async with self.get_semaphore():
                future = pool.schedule(
                    get_text, args=[data, lang, attachment_id], timeout=self.timeout
                )
                log.debug(
                    f"OCR worker for attachment '{attachment_id}' was submitted to the pool"
                )
                result = await asyncio.wrap_future(future)
                log.debug(f"OCR worker for attachment '{attachment_id}' is done")
                return result
        except TimeoutError:
            log.warning(f"OCR worker for attachment '{attachment_id}' timed out")
            return
        except asyncio.CancelledError:
            if future and not future.done():
                future.cancel()
            log.debug(f"OCR worker for attachment '{attachment_id}' was cancelled")
            raise
        except Exception:
            log.exception(
                f"OCR worker for attachment '{attachment_id}' ran into an error"
            )
            return

    async def _ocr(self, context: AutomodContext) -> Optional[AttachmentID]:
        # We need image attachments in context
        image_attachments = await context.fetch_attachments_with_type(*IMAGE_MIME_TYPES)
        if not image_attachments:
            return

        # Create `lang` string from languages and scripts
        lang: str = "+".join(v for v in chain(self.languages, self.scripts))

        # Submit OCR tasks to the process pool
        assert is_commander_bot(context.bot)
        pool = context.bot.pool
        log = context.log
        tasks = [
            asyncio.create_task(self._ocr_worker(pool, log, attachment.id, data, lang))
            for attachment, data, _ in image_attachments
        ]

        # Check OCR results as they come in
        # This may raise a `TimeoutError`, but it *should* be caught in the guild state
        try:
            async for completed_task in asyncio.as_completed(tasks):
                try:
                    # Check if the text passes the condition and return the attachment ID
                    if task_result := await completed_task:
                        text, attachment_id = task_result
                        if self._check_ocr_result(text):
                            return attachment_id
                except Exception:
                    continue
        finally:
            # Cancel any remaining tasks
            for t in tasks:
                if not t.done():
                    t.cancel()

            # Wait for those tasks to be cleaned up
            await asyncio.gather(*tasks, return_exceptions=True)

    @override
    async def check(self, context: AutomodContext) -> bool:
        # Throw an exception if OCR isn't supported
        if not SUPPORTS_OCR:
            raise OCRNotSupported

        # OCR image attachments
        if attachment_id := await self._ocr(context):
            context.metadata.flagged_attachments.append(attachment_id)
            return True

        # If we got this far, none of the attachments passed the condition
        return False
