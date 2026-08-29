from collections.abc import Callable
from typing import Any, Optional

__all__ = ("ValueFormatter",)


class ValueFormatter:
    def __init__(self, value: Any, formatter: Optional[Callable[[Any], str]] = None):
        self.value = value
        self.formatter = formatter or str

    def __str__(self):
        return self.formatter(self.value)
