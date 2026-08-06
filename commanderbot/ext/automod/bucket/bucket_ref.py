from typing import Any, Optional, overload

from pydantic import BaseModel, Field, GetCoreSchemaHandler
from pydantic_core import core_schema

from commanderbot.ext.automod.automod_context import AutomodContext
from commanderbot.ext.automod.bucket import AutomodBucket

__all__ = ("AutomodBucketRef",)


class AutomodBucketRef(BaseModel):
    """
    A reference to a bucket, by name.
    """

    name: str = Field(min_length=1)
    """The name of the bucket."""

    @overload
    async def resolve(self, context: AutomodContext) -> AutomodBucket:
        """
        Resolve the bucket. Will throw an expection if it's not found.
        """

    @overload
    async def resolve[BucketType = AutomodBucket](
        self, context: AutomodContext, bucket_type: type[BucketType]
    ) -> BucketType:
        """
        Resolve the bucket and require it to have a specific type. Will throw an expection if it's not found.
        """

    async def resolve[BucketType = AutomodBucket](
        self, context: AutomodContext, bucket_type: Optional[type[BucketType]] = None
    ) -> AutomodBucket | BucketType:
        # Get store from context
        guild = context.state.guild
        store = context.state.store

        # Resolve the bucket
        if bucket_type is not None:
            return await store.require_bucket_with_type(guild, self.name, bucket_type)
        return await store.require_bucket(guild, self.name)

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        default_schema = handler(source_type)
        from_str_schema = core_schema.chain_schema(
            [
                core_schema.str_schema(min_length=1),
                core_schema.no_info_plain_validator_function(
                    lambda data: cls(name=data)
                ),
            ]
        )

        return core_schema.json_or_python_schema(
            json_schema=from_str_schema,
            python_schema=core_schema.union_schema(
                [
                    core_schema.is_instance_schema(cls),
                    from_str_schema,
                    default_schema,
                ]
            ),
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda ref: ref.name
            ),
        )
