from typing import Optional

from discord import Reaction
from pydantic import BaseModel, ConfigDict, Field

from commanderbot.ext.automod.guards.integer_range import IntegerRangeGuard

__all__ = ("ReactionsGuard",)


class ReactionsGuard(BaseModel):
    """
    Checks whether a reaction matches a set of reactions.
    """

    model_config = ConfigDict(use_attribute_docstrings=True)

    include: set[str] = Field(default_factory=set)
    """The reactions to include. A reaction will match if it's in this set."""

    exclude: set[str] = Field(default_factory=set)
    """The reactions to exclude. A reaction will match if it's not in this set."""

    count: Optional[IntegerRangeGuard] = None
    """The number of times the reaction was made."""

    def _ignore_by_includes(self, reaction: Reaction) -> bool:
        if self.include:
            return str(reaction.emoji) not in self.include
        return False

    def _ignore_by_excludes(self, reaction: Reaction) -> bool:
        if self.exclude:
            return str(reaction.emoji) in self.exclude
        return False

    def _ignore_by_count(self, reaction: Reaction) -> bool:
        if self.count:
            return self.count.excludes(reaction.count)
        return False

    def ignore(self, reaction: Optional[Reaction]) -> bool:
        """Determine whether to ignore the reaction based on the emoji and count."""
        if not reaction:
            return False

        return (
            self._ignore_by_includes(reaction)
            or self._ignore_by_excludes(reaction)
            or self._ignore_by_count(reaction)
        )
