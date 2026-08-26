from typing import Optional

import discord
from pydantic import BaseModel, ConfigDict, Field

from commanderbot.lib.types import DiscordAutomodRuleID

__all__ = ("DiscordAutomodRulesGuard",)


class DiscordAutomodRulesGuard(BaseModel):
    """
    Checks whether a Discord automod rule matches a set of Discord automod rules.
    """

    model_config = ConfigDict(use_attribute_docstrings=True)

    include: set[DiscordAutomodRuleID] = Field(default_factory=set)
    """The Discord automod rules to include. A rule will match if it's in this set."""

    exclude: set[DiscordAutomodRuleID] = Field(default_factory=set)
    """The Discord automod rules to exclude. A rule will match if it's not in this set."""

    def _ignore_by_includes(self, rule_id: DiscordAutomodRuleID) -> bool:
        if self.include:
            return rule_id not in self.include
        return False

    def _ignore_by_excludes(self, rule_id: DiscordAutomodRuleID) -> bool:
        if self.exclude:
            return rule_id in self.exclude
        return False

    def ignore(self, rule: Optional[discord.AutoModRule | DiscordAutomodRuleID]):
        """Determine whether to ignore the Discord automod rule."""
        if not rule:
            return False

        # Get the ID of the rule
        rule_id = rule.id if isinstance(rule, discord.AutoModRule) else rule

        return self._ignore_by_includes(rule_id) or self._ignore_by_excludes(rule_id)
