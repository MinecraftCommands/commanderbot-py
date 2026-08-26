from datetime import timedelta
from typing import Annotated

from pydantic import TypeAdapter, WithJsonSchema

__all__ = (
    "Timedelta",
    "TimedeltaAdapter",
)

type Timedelta = Annotated[
    timedelta,
    WithJsonSchema(
        {
            "anyOf": [
                {
                    "type": "number",
                    "examples": [5, 1.0, 3.5],
                },
                {
                    "type": "string",
                    "format": "iso-8061-duration",
                    "pattern": r"^[+-]?P(?:(?:\d+W)|(?=.*(?:\d+[YMWDHMS]))(?:\d+Y)?(?:\d+M)?(?:\d+W)?(?:\d+D)?(?:T(?:\d+H(?:\d+M(?:\d+S)?)?|\d+M(?:\d+S)?|\d+S))?)",
                    "examples": ["PT5H30M", "PT2DT5H15M10S", "P2Y5M2W1DT4H20M"],
                },
                {
                    "type": "string",
                    "format": "duration",
                    "pattern": r"^[+-]?\s*(?:(?:\d+)\s*(?i:(?:days?|d))\s*,?\s*)?\d{2}:\d{2}:\d{2}(?:\.\d+)?$",
                    "examples": ["05:30:00", "2 days, 05:15:00", "5d, 04:20:00"],
                },
            ]
        },
        mode="validation",
    ),
]
"""
An alias for `datetime.timedelta`, but with a Json schema for Pydantic. 
"""

TimedeltaAdapter = TypeAdapter(Timedelta)
"""
A Pydantic type adapter that lets you de/serialize `Timedelta` outside of a Pydantic `BaseModel`.
"""
