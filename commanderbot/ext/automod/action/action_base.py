from abc import ABC, abstractmethod
from typing import Optional

from pydantic import BaseModel, ConfigDict

from commanderbot.ext.automod.automod_context import AutomodContext

__all__ = ("AutomodAction",)


class AutomodAction(ABC, BaseModel):
    """
    Base class for all automod actions.

    An action defines a task to perform when conditions pass.
    """

    model_config = ConfigDict(use_attribute_docstrings=True)

    type: str
    """The action type."""

    description: Optional[str] = None
    """Describe what the action does."""

    disabled: bool = False
    """Is the action disabled?"""

    @abstractmethod
    async def apply(self, context: AutomodContext):
        """Apply the action."""
        pass
