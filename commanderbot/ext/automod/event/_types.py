from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from commanderbot.ext.automod.automod_guild_state import AutomodGuildState

    type AutomodGuildStateRef = AutomodGuildState
else:
    type AutomodGuildStateRef = Any
