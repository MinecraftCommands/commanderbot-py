from typing import Literal, override

from pydantic import Field

from commanderbot.ext.automod import buckets
from commanderbot.ext.automod.automod_context import AutomodContext
from commanderbot.ext.automod.bucket import AutomodBucketRef
from commanderbot.ext.automod.condition import AutomodCondition
from commanderbot.ext.automod.constants import IMAGE_MIME_TYPES

__all__ = ("HasFlaggedImageAttachments",)


class HasFlaggedImageAttachments(AutomodCondition):
    """
    Check if any image attachments in context have already been flagged.
    """

    type: Literal["has_flagged_image_attachments"]

    bucket: AutomodBucketRef
    """The bucket being used to track flagged image attachments."""

    threshold: int = Field(default=0, ge=0)
    """
    Hamming distance threshold.

    - `0-4`: Identical or extremely similar.
    - `5-10`: Very similar.
    - `11-20`: Potentially a variation or shares similar structures.
    - `21+`: Completely different images.
    """

    @override
    async def check(self, context: AutomodContext) -> bool:
        # We need to have image attachments in context
        image_attachments = await context.fetch_attachments_with_type(*IMAGE_MIME_TYPES)
        if not image_attachments:
            return False

        # Check if any image attachments are in the bucket
        bucket = await self.bucket.resolve(context, buckets.FlaggedImageAttachments)
        for attachment, _, phash in image_attachments:
            assert phash is not None
            if bucket.is_flagged(attachment) or bucket.is_flagged_phash(
                phash, self.threshold
            ):
                return True

        # If we got this far, none of the image attachments have been flagged
        return False
