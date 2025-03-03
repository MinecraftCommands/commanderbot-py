from dataclasses import dataclass

from commanderbot.ext.friday.friday_guild_state import FridayGuildState
from commanderbot.ext.friday.friday_store import FridayStore
from commanderbot.lib.cogs import GuildPartitionedCogState


@dataclass
class FridayState(GuildPartitionedCogState[FridayGuildState]):
    """
    Encapsulates the state and logic of the friday cog, for each guild.

    Attributes
    -----------
    store
        The store used to interface with persistent data in a database-agnostic way.
    """

    store: FridayStore