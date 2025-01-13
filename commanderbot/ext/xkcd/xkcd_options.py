from dataclasses import dataclass
from typing import Any, Optional, Self

from commanderbot.lib import FromDataMixin


@dataclass
class XKCDOptions(FromDataMixin):
    cache_valid_for: int = 1
    comic_404_image_url: Optional[str] = None

    # @implements FromDataMixin
    @classmethod
    def try_from_data(cls, data: Any) -> Optional[Self]:
        if isinstance(data, dict):
            return cls(
                cache_valid_for=data.get("cache_valid_for", 1),
                comic_404_image_url=data.get("comic_404_image_url"),
            )
