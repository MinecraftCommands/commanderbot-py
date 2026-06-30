from typing import TYPE_CHECKING, Any

__all__ = ("AutomodGuildStateRef", "AutomodRuleRef")

if TYPE_CHECKING:
    from commanderbot.ext.automod.automod_guild_state import AutomodGuildState
    from commanderbot.ext.automod.rule import AutomodRule

    type AutomodGuildStateRef = AutomodGuildState
    """A reference to an `AutomodGuildStateRef` for type checkers."""

    type AutomodRuleRef = AutomodRule
    """A reference to an `AutomodRule` for type checkers."""
else:
    type AutomodGuildStateRef = Any
    type AutomodRuleRef = Any
