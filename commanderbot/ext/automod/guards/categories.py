from typing import Optional

from discord import CategoryChannel
from pydantic import BaseModel, ConfigDict, Field

from commanderbot.lib.types import CategoryID

__all__ = ("CategoriesGuard",)


class CategoriesGuard(BaseModel):
    """
    Checks whether a category matches a set of categories.
    """

    model_config = ConfigDict(use_attribute_docstrings=True)

    include: set[CategoryID] = Field(default_factory=set)
    """The categories to include. A category will match if it's in this set."""

    exclude: set[CategoryID] = Field(default_factory=set)
    """The categories to exclude. A category will match if it's not in this set."""

    def _ignore_by_includes(self, category: CategoryChannel) -> bool:
        if self.include:
            return category.id not in self.include
        return False

    def _ignore_by_excludes(self, category: CategoryChannel) -> bool:
        if self.exclude:
            return category.id in self.exclude
        return False

    def ignore(self, category: Optional[CategoryChannel]) -> bool:
        """Determine whether to ignore the category."""
        if not category:
            return False

        return self._ignore_by_includes(category) or self._ignore_by_excludes(category)
