from typing import Any, Optional, Self

from pydantic import BaseModel, ConfigDict, GetCoreSchemaHandler
from pydantic_core import core_schema

from commanderbot.ext.automod.automod_exceptions import AutomodValidationError

__all__ = ("IntegerRangeGuard",)


class IntegerRangeGuard(BaseModel):
    """
    An integer range with optional upper and lower bounds.
    """

    model_config = ConfigDict(use_attribute_docstrings=True)

    min: Optional[int] = None
    """The lower bound of the range (inclusive)."""

    max: Optional[int] = None
    """The upper bound of the range (inclusive)."""

    def includes(self, value: int) -> bool:
        if self.min is not None and value < self.min:
            return False

        if self.max is not None and value > self.max:
            return False

        return True

    def excludes(self, value: int) -> bool:
        return not self.includes(value)

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        def validate_min_max(guard: Self) -> Self:
            if guard.min and guard.max and guard.min > guard.max:
                raise AutomodValidationError("'min' is greater than 'max'")
            return guard

        default_schema = handler(source_type)
        from_dict_schema = core_schema.no_info_after_validator_function(
            validate_min_max, default_schema
        )

        from_int_schema = core_schema.chain_schema(
            steps=[
                core_schema.int_schema(),
                core_schema.no_info_plain_validator_function(
                    lambda data: cls(min=data, max=data)
                ),
            ],
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda guard: guard.min
            ),
        )

        return core_schema.json_or_python_schema(
            json_schema=core_schema.union_schema(
                [
                    from_int_schema,
                    from_dict_schema,
                ]
            ),
            python_schema=core_schema.union_schema(
                [
                    core_schema.is_instance_schema(cls),
                    from_int_schema,
                    from_dict_schema,
                ]
            ),
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda guard: {"min": guard.min, "max": guard.max}
            ),
        )
