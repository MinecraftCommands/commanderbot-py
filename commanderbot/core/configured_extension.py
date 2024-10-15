from dataclasses import dataclass
from typing import Any, Optional, Self

from commanderbot.lib import FromDataMixin, JsonSerializable, utils
from commanderbot.lib.types import JsonObject


@dataclass
class ConfiguredExtension(JsonSerializable, FromDataMixin):
    """
    Represents an extension with an optional config.

    Attributes
    ----------
    name: :class:`str`
        The name of this extension (Should be the same as its import path).
    required: :class:`bool`
        Whether this extension is required or not. It doesn't affect loading/unloading/reloading this extension,
        but you're free to choose how to handle this attribute in your code. Defaults to `False`.
    disabled: :class:`bool`
        Whether this extension is disabled or not. Defaults to `False`.
    options: :class:`Optional[JsonObject]`
        Options for this extension. Defaults to `None`.
    """

    name: str
    required: bool = False
    disabled: bool = False
    options: Optional[JsonObject] = None

    # @implements FromDataMixin
    @classmethod
    def try_from_data(cls, data: Any) -> Optional[Self]:
        if isinstance(data, str):
            # Extensions starting with a `$` are required.
            if data.startswith("$"):
                return cls(name=data[1:], required=True)
            # Extensions starting with a `!` are disabled.
            elif data.startswith("!"):
                return cls(name=data[1:], disabled=True)
            else:
                return cls(name=data)
        elif isinstance(data, dict):
            return cls(**data)

    # @implements JsonSerializable
    def to_json(self) -> Any:
        return utils.dict_without_falsies(
            name=self.name,
            required=self.required,
            disabled=self.disabled,
            options=self.options,
        )
