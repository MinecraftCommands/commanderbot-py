from dataclasses import dataclass
from typing import Any, Optional, TypeVar

from discord import Member

from commanderbot.ext.automod.automod_event import AutomodEvent
from commanderbot.ext.automod.condition import Condition
from commanderbot.ext.automod.conditions.abc.target_roles_base import TargetRolesBase

ST = TypeVar("ST")


@dataclass
class ActorRoles(TargetRolesBase):
    """
    Check if the actor in context has certain roles.

    Attributes
    ----------
    roles
        The roles to match against.
    """

    def get_target(self, event: AutomodEvent) -> Optional[Member]:
        return event.actor


def create_condition(data: Any) -> Condition:
    return ActorRoles.from_data(data)
