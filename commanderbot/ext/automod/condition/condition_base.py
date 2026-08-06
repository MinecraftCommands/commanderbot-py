from abc import ABC, abstractmethod
from typing import Optional

from pydantic import BaseModel, ConfigDict

from commanderbot.ext.automod.automod_context import AutomodContext

__all__ = ("AutomodCondition",)


class AutomodCondition(ABC, BaseModel):
    """
    Base class for all automod conditions.

    A condition is a predicate that must pass in order to run actions.
    """

    model_config = ConfigDict(use_attribute_docstrings=True)

    type: str
    """The condition type."""

    description: Optional[str] = None
    """Describe what the condition does."""

    disabled: bool = False
    """Is the condition disabled?"""

    @abstractmethod
    async def check(self, context: AutomodContext) -> bool:
        """Check whether the condition passes."""
        ...
