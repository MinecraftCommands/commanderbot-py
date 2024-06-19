import asyncio
import json
from pathlib import Path
from typing import Any, Optional

from commanderbot.lib.extended_json_encoder import ExtendedJsonEncoder
from commanderbot.lib.types import JsonObject


def to_data(obj: Any) -> Any:
    # TODO There's got to be a direct way to do this... #optimize
    return json.loads(json.dumps(obj, cls=ExtendedJsonEncoder))


def json_load(path: Path) -> JsonObject:
    with open(path) as fp:
        data = json.load(fp)
    return data


async def json_load_async(path: Path) -> JsonObject:
    return await asyncio.to_thread(json_load, path)


def json_dump(
    data: JsonObject,
    path: Path,
    mkdir: bool = False,
    indent: Optional[int] = None,
):
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
    await asyncio.to_thread(json_dump, data, path, mkdir, indent)


def json_dumps(data: JsonObject) -> str:
    return json.dumps(data, cls=ExtendedJsonEncoder)


async def json_dumps_async(data: JsonObject) -> str:
    return await asyncio.to_thread(json_dumps, data)
