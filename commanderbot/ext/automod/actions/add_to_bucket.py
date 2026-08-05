from typing import Literal, override

from commanderbot.ext.automod.action import AutomodAction
from commanderbot.ext.automod.automod_context import AutomodContext
from commanderbot.ext.automod.bucket import AutomodBucketRef

__all__ = ("AddToBucket",)


class AddToBucket(AutomodAction):
    """
    Add any relevant data in context to a bucket.
    """

    type: Literal["add_to_bucket"]

    bucket: AutomodBucketRef
    """The bucket to add to."""

    @override
    async def apply(self, context: AutomodContext):
        # Get the bucket and add context data to it
        bucket = await self.bucket.resolve(context)
        if not bucket.disabled:
            await bucket.add(context)
