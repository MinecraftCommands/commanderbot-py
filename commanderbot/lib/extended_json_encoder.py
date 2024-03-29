import dataclasses
import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Set

import discord

from commanderbot.lib.json_serializable import JsonSerializable
from commanderbot.lib.utils import timedelta_to_dict


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

    def convert_set(self, obj: Set[Any]) -> List[Any]:
        return list(obj)

    def convert_datetime(self, obj: datetime) -> str:
        return obj.isoformat()

    def convert_timedelta(self, obj: timedelta) -> Dict[str, Any]:
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
