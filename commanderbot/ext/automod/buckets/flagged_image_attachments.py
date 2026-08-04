from datetime import datetime
from typing import Literal, override

from discord import Attachment
from discord.utils import utcnow
from pydantic import BaseModel, Field

from commanderbot.ext.automod.automod_context import AutomodContext
from commanderbot.ext.automod.bucket import AutomodBucket
from commanderbot.ext.automod.constants import IMAGE_MIME_TYPES
from commanderbot.lib.image_hash import ImageHash
from commanderbot.lib.types import AttachmentID, Timedelta

__all__ = ("FlaggedImageAttachments",)


class FlaggedImageAttachment(BaseModel):
    attachment_id: AttachmentID
    phash: ImageHash
    time: datetime


class FlaggedImageAttachments(AutomodBucket):
    """
    Track image attachments that were flagged by various conditions.
    """

    type: Literal["flagged_image_attachments"]

    lifetime: Timedelta
    """
    How long to store flagged image attachments. Longer durations are able to store more
    image attachments for potential queries, but take more memory on average.
    """

    attachments: dict[AttachmentID, FlaggedImageAttachment] = Field(
        default_factory=dict, exclude_if=lambda v: not v
    )

    def _clean_up(self):
        cutoff = utcnow() - self.lifetime
        for attachment_id in list(self.attachments.keys()):
            if self.attachments[attachment_id].time < cutoff:
                del self.attachments[attachment_id]

    def is_flagged(self, image_attachment: Attachment) -> bool:
        return image_attachment.id in self.attachments

    def is_flagged_phash(self, phash: ImageHash, max_hamming_distance: int = 0) -> bool:
        for flagged_attachment in self.attachments.values():
            if flagged_attachment.phash - phash <= max_hamming_distance:
                return True
        return False

    @override
    async def add(self, context: AutomodContext):
        # We need image attachments in context
        image_attachments = await context.fetch_attachments_with_type(*IMAGE_MIME_TYPES)
        if not image_attachments:
            return

        # Clean up expired image attachments
        self._clean_up()

        # Add flagged image attachments to bucket
        flagged_at = utcnow()
        for image_attachment, _, phash in image_attachments:
            # The image attachment needs to have a phash
            assert phash is not None

            # Skip image attachments that weren't flagged
            if image_attachment.id not in context.metadata.flagged_attachments:
                continue

            # If the image attachment was already stored, update its time
            if flagged := self.attachments.get(image_attachment.id):
                flagged.time = flagged_at
                continue

            # Otherwise, add a new entry
            flagged = FlaggedImageAttachment(
                attachment_id=image_attachment.id, phash=phash, time=flagged_at
            )
            self.attachments[image_attachment.id] = flagged

    @override
    def clear(self):
        self.attachments.clear()
