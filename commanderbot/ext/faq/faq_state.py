from dataclasses import dataclass

from commanderbot.ext.faq.faq_guild_state import FaqGuildState
from commanderbot.ext.faq.faq_store import FaqStore
from commanderbot.lib.cogs import GuildPartitionedCogState


@dataclass
class FaqState(GuildPartitionedCogState[FaqGuildState]):
    """
    Encapsulates the state and logic of the faq cog, for each guild.

    Attributes
    -----------
    store
        The store used to interface with persistent data in a database-agnostic way.
    """

    store: FaqStore
