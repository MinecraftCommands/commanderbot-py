from typing import Literal

from commanderbot.ext.automod import events
from commanderbot.ext.automod.triggers.reaction import Reaction

__all__ = ("ReactionAdded",)


class ReactionAdded(Reaction):
    """
    Triggers when a reaction is added.
    """

    type: Literal["reaction_added"] = "reaction_added"
    event_types = (events.ReactionAdded,)
