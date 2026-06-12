from pathlib import Path
from typing import Annotated, Literal, Optional, TypeIs

from pydantic import BaseModel, BeforeValidator, Field

__all__ = (
    "InMemoryDatabaseOptions",
    "JsonFileDatabaseOptions",
    "JsonDBOptions",
)


class InMemoryDatabaseOptions(BaseModel):
    type: Literal["in_memory"] = "in_memory"


class JsonFileDatabaseOptions(BaseModel):
    type: Literal["json_file"] = "json_file"
    path: Path
    no_init: bool = False
    indent: Optional[int] = None


def validate_options(data: Optional[str | dict]) -> dict:
    if data is None:
        return {"type": "in_memory"}
    elif isinstance(data, str):
        return {"type": "json_file", "path": data}
    return data


JsonDBOptions = Annotated[
    InMemoryDatabaseOptions | JsonFileDatabaseOptions,
    Field(default_factory=InMemoryDatabaseOptions, discriminator="type"),
    BeforeValidator(validate_options),
]


def is_in_memory_options(obj: object) -> TypeIs[InMemoryDatabaseOptions]:
    return isinstance(obj, InMemoryDatabaseOptions)


def is_json_file_options(obj: object) -> TypeIs[JsonFileDatabaseOptions]:
    return isinstance(obj, JsonFileDatabaseOptions)
