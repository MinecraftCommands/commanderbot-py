from datetime import datetime

from pydantic import BaseModel, ConfigDict

from commanderbot.lib.types import UserID

__all__ = ("AutomodRuleMetadata",)


class AutomodRuleMetadata(BaseModel):
    """
    Contains metadata about an automod rule. This is separate from the rule
    so users can't modify it.
    """

    model_config = ConfigDict(use_attribute_docstrings=True)

    name: str
    """The name of the rule this metadata is for"""

    hits: int
    """How many times the rule's conditions have passed and actions have run."""

    added_by_id: UserID
    """The ID of the user who created the rule."""

    modified_by_id: UserID
    """The ID of the last user that modified the rule."""

    added_on: datetime
    """The `datetime` the rule was created."""

    modified_on: datetime
    """The last `datetime` the rule was modified."""
