import asyncio
import dataclasses
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

import discord

from commanderbot.lib.json_serializable import JsonSerializable
from commanderbot.lib.types import JsonObject
from commanderbot.lib.utils.timedeltas import timedelta_to_dict

__all__ = (
    "ExtendedJsonEncoder",
    "to_data",
    "json_load",
    "json_load_async",
    "json_dump",
    "json_dump_async",
    "json_dumps",
    "json_dumps_async",
)


class ExtendedJsonEncoder(json.JSONEncoder):
    """
    Extended JSON encoder with frequently-used logic built-in.

    Converts the following additional objects, in order of precedence:
    1. A subclass of `JsonSerializable` is converted using `.to_json()`
    2. A `set` is converted into a list
    3. A `datatime.datetime` is converted into a string using `.isoformat()`
    4. A `datatime.timedelta` is converted into an object using `timedelta_to_dict()`
    5. A `dataclasses.dataclass` is converted using `dataclasses.asdict()`
    6. A `discord.Color` is converted into hex format `#FFFFFF`
    """

    def default(self, obj: Any) -> Any:
        if isinstance(obj, JsonSerializable):
            return obj.to_json()
        if isinstance(obj, set):
            return self.convert_set(obj)
        if isinstance(obj, datetime):
            return self.convert_datetime(obj)
        if isinstance(obj, timedelta):
            return self.convert_timedelta(obj)
        if dataclasses.is_dataclass(obj):
            return self.convert_dataclass(obj)
        if isinstance(obj, discord.Color):
            return self.convert_color(obj)
        return super().default(obj)

    def convert_set(self, obj: set[Any]) -> list[Any]:
        return list(obj)

    def convert_datetime(self, obj: datetime) -> str:
        return obj.isoformat()

    def convert_timedelta(self, obj: timedelta) -> dict[str, Any]:
        return timedelta_to_dict(obj)

    def convert_dataclass(self, obj: Any) -> Any:
        # NOTE We can't use `dataclasses.asdict` because it recurses implicitly.
        # Which means there's no way to intercept the serialization of nested
        # dataclasses, so e.g. the `to_json()` of any nested dataclasses will be
        # bypassed entirely. Instead, we use `__dict__` to serialize one layer of
        # dataclass at a time.
        return obj.__dict__

    def convert_color(self, obj: discord.Color) -> Any:
        # Takes a `discord.Color` so this works with `commanderbot.lib.color` too.
        return str(obj)


def to_data(obj: Any) -> Any:
    # TODO There's got to be a direct way to do this... #optimize
    return json.loads(json.dumps(obj, cls=ExtendedJsonEncoder))


def json_load(path: Path) -> JsonObject:
    """
    Deserialize a json file located at `path`.
    """
    with open(path) as fp:
        data = json.load(fp)
    return data


async def json_load_async(path: Path) -> JsonObject:
    """
    Asynchronously deserialize a json file located at `path`.
    """
    return await asyncio.to_thread(json_load, path)


def json_dump(
    data: JsonObject,
    path: Path,
    mkdir: bool = False,
    indent: Optional[int] = None,
):
    """
    Serialize a Json-like object to a json file located at `path`.
    """
    if mkdir:
        path.parent.mkdir(parents=True, exist_ok=True)
    # NOTE Serialize the JSON first, otherwise invalid data may corrupt the file.
    output = json.dumps(data, indent=indent, cls=ExtendedJsonEncoder)
    with open(path, "w") as fp:
        fp.write(output)


async def json_dump_async(
    data: JsonObject,
    path: Path,
    mkdir: bool = False,
    indent: Optional[int] = None,
):
    """
    Asynchronously serialize a Json-like object to a json file located at `path`.
    """
    await asyncio.to_thread(json_dump, data, path, mkdir, indent)


def json_dumps(data: JsonObject) -> str:
    """
    Serialize a Json-like object to a string.
    """
    return json.dumps(data, cls=ExtendedJsonEncoder)


async def json_dumps_async(data: JsonObject) -> str:
    """
    Asynchronously serialize a Json-like object to a string.
    """
    return await asyncio.to_thread(json_dumps, data)
