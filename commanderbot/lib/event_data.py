from dataclasses import dataclass
from typing import Any


@dataclass
class EventData:
    name: str
    args: tuple[Any, ...]
    kwargs: dict[str, Any]

    def format_codeblock(self) -> str:
        lines = [
            "```python",
            repr(self),
            "```",
        ]
        return "\n".join(lines)
