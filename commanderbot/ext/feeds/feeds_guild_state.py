from dataclasses import dataclass

from commanderbot.ext.feeds.feeds_store import FeedsStore
from commanderbot.lib.cogs import CogGuildState


@dataclass
class FeedsGuildState(CogGuildState):
    """
    Encapsulates the state and logic of the feeds cog, at the guild level.

    Attributes
    -----------
    store
        The store used to interface with persistent data in a database-agnostic way.
    """

    store: FeedsStore
