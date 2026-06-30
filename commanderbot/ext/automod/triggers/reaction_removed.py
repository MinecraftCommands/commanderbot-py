from typing import Literal

from commanderbot.ext.automod import events
from commanderbot.ext.automod.triggers.reaction import Reaction

__all__ = ("ReactionRemoved",)


class ReactionRemoved(Reaction):
    """
    Triggers when a reaction is removed.
    """

    type: Literal["reaction_removed"] = "reaction_removed"
    event_types = (events.ReactionRemoved,)
