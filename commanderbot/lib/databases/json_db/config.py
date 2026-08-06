from pathlib import Path
from typing import Annotated, Any, Literal, Optional, TypeIs

from pydantic import BaseModel, BeforeValidator, Field

__all__ = (
    "InMemoryDatabaseOptions",
    "JsonDBOptions",
    "JsonFileDatabaseOptions",
)


class InMemoryDatabaseOptions(BaseModel):
    type: Literal["in_memory"]


class JsonFileDatabaseOptions(BaseModel):
    type: Literal["json_file"]
    path: Path
    no_init: bool = False
    indent: Optional[int] = None
    exclude_defaults: bool = True
    exclude_none: bool = False


def validate_options(data: Any) -> Any:
    if data is None:
        return {"type": "in_memory"}
    elif isinstance(data, str):
        return {"type": "json_file", "path": data}
    return data


JsonDBOptions = Annotated[
    InMemoryDatabaseOptions | JsonFileDatabaseOptions,
    Field(
        discriminator="type",
        default_factory=lambda: InMemoryDatabaseOptions(type="in_memory"),
    ),
    BeforeValidator(validate_options),
]


def is_in_memory_options(obj: object) -> TypeIs[InMemoryDatabaseOptions]:
    return isinstance(obj, InMemoryDatabaseOptions)


def is_json_file_options(obj: object) -> TypeIs[JsonFileDatabaseOptions]:
    return isinstance(obj, JsonFileDatabaseOptions)
