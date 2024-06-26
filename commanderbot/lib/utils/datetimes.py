from datetime import datetime
from typing import Any, Optional

from commanderbot.lib.exceptions import MalformedData
from commanderbot.lib.types import JsonObject

__all__ = (
    "try_datetime_from_data",
    "datetime_from_data",
    "datetime_from_field",
    "datetime_from_field_optional",
)


def try_datetime_from_data(data: Any) -> Optional[datetime]:
    if isinstance(data, str):
        return datetime.fromisoformat(data)


def datetime_from_data(data: Any) -> datetime:
    try:
        if (maybe_from_data := try_datetime_from_data(data)) is not None:
            return maybe_from_data
    except Exception as ex:
        raise MalformedData(datetime, data) from ex
    raise MalformedData(datetime, data)


def datetime_from_field(data: JsonObject, key: str) -> datetime:
    return datetime_from_data(data[key])


def datetime_from_field_optional(data: JsonObject, key: str) -> Optional[datetime]:
    if raw_value := data.get(key):
        return datetime_from_data(raw_value)
