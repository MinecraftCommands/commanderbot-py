from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional, Self

from commanderbot.lib import FromDataMixin


@dataclass
class ConfiguredExtension(FromDataMixin):
    name: str
    disabled: bool = False
    options: Optional[dict[str, Any]] = None

    @classmethod
    def try_from_data(cls, data: Any) -> Optional[Self]:
        if isinstance(data, str):
            # Extensions starting with a `!` are disabled.
            disabled = data.startswith("!")
            name = data[1:] if disabled else data
            return cls(name=name, disabled=disabled)
        elif isinstance(data, dict):
            return cls(**data)
