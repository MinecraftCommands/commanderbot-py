from abc import ABC, abstractmethod
from typing import Optional

from pydantic import BaseModel, ConfigDict

from commanderbot.ext.automod.automod_context import AutomodContext

__all__ = ("AutomodBucket",)


class AutomodBucket(ABC, BaseModel):
    """
    Base class for all automod buckets.

    A bucket can be used to carry state through multiple events.
    """

    model_config = ConfigDict(use_attribute_docstrings=True)

    type: str
    """The bucket type."""

    name: str
    """The name of the bucket."""

    description: Optional[str] = None
    """Describe what the bucket is for."""

    disabled: bool = False
    """Is the bucket disabled?"""

    @abstractmethod
    async def add(self, context: AutomodContext):
        """Modify the bucket using context data."""
        ...

    @abstractmethod
    async def clear(self):
        """Clear all data in the bucket."""
        ...
