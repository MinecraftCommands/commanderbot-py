from dataclasses import dataclass
from typing import Any, Optional, Self

from commanderbot.lib import FromDataMixin

@dataclass
class McdocOptions(FromDataMixin):
    symbols_url: str
    manifest_url: str
    emoji_prefix: str
    icon_url: Optional[str]

    @classmethod
    def try_from_data(cls, data: Any) -> Optional[Self]:
        if isinstance(data, dict):
            return cls(
                symbols_url=data["symbols_url"],
                manifest_url=data["manifest_url"],
                emoji_prefix=data["emoji_prefix"],
                icon_url=data.get("icon_url", None),
            )
