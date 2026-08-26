from typing import Annotated

from pydantic import Field

from commanderbot.ext.automod import buckets

__all__ = ("AutomodBucketType",)

type _AutomodBucketType = (buckets.FlaggedImageAttachments | buckets.MessageHistory)

type AutomodBucketType = Annotated[_AutomodBucketType, Field(discriminator="type")]
