from abc import ABC, abstractmethod
from typing import Any, Optional, Self

from commanderbot.lib.exceptions import MalformedData
from commanderbot.lib.json import JsonObject

__all__ = ("FromDataMixin",)


class FromDataMixin(ABC):
    @classmethod
    @abstractmethod
    def try_from_data(cls, data: Any) -> Optional[Self]:
        """Override this to return an instance of the class given valid input."""

    @classmethod
    def from_data(cls, data: Any) -> Self:
        try:
            if (maybe_from_data := cls.try_from_data(data)) is not None:
                return maybe_from_data
        except Exception as ex:
            raise MalformedData(cls, data) from ex
        raise MalformedData(cls, data)

    @classmethod
    def from_field(cls, data: JsonObject, key: str) -> Self:
        return cls.from_data(data[key])

    @classmethod
    def from_field_optional(cls, data: JsonObject, key: str) -> Optional[Self]:
        if raw_value := data.get(key):
            return cls.from_data(raw_value)
