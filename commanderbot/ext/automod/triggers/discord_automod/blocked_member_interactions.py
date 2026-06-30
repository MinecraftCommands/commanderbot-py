from typing import Literal, Optional, override

from commanderbot.ext.automod import events
from commanderbot.ext.automod.event import AutomodEvent
from commanderbot.ext.automod.guards import DiscordAutomodRulesGuard, RolesGuard
from commanderbot.ext.automod.trigger import AutomodTrigger
from commanderbot.ext.automod.types import AutomodRuleRef

__all__ = ("DiscordAutomodBlockedMemberInteractions",)


class DiscordAutomodBlockedMemberInteractions(AutomodTrigger):
    """
    Triggers when Discord's automod blocks member interactions.
    """

    type: Literal["discord_automod_blocked_member_interactions"] = (
        "discord_automod_blocked_member_interactions"
    )
    event_types = (events.DiscordAutomodBlockedMemberInteractions,)

    rules: Optional[DiscordAutomodRulesGuard] = None
    """The Discord automod rules to match against. If empty, all rules will match."""

    roles: Optional[RolesGuard] = None
    """The roles of the blocked user to match against. If empty, all roles will match."""

    @override
    async def ignore(self, rule: AutomodRuleRef, event: AutomodEvent) -> bool:
        assert isinstance(event, events.DiscordAutomodBlockedMemberInteractions)

        if self.rules and self.rules.ignore(event.rule_id):
            return True

        if self.roles and self.roles.ignore(event.member):
            return True

        return False
