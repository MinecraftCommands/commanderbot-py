from typing import Annotated, Any

import imagehash
from pydantic import PlainSerializer, PlainValidator

__all__ = ("ImageHash",)


def _validate_image_hash(data: Any) -> imagehash.ImageHash:
    if isinstance(data, imagehash.ImageHash):
        return data
    elif isinstance(data, str):
        return imagehash.hex_to_hash(data)
    raise ValueError(f"'{data}' is not a valid 'imagehash.ImageHash'")


ImageHash = Annotated[
    imagehash.ImageHash,
    PlainValidator(_validate_image_hash, json_schema_input_type=str),
    PlainSerializer(lambda value: str(value), return_type=str),
]
