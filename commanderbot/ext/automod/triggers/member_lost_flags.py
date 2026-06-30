from typing import Literal, Optional, override

from commanderbot.ext.automod import events
from commanderbot.ext.automod.event import AutomodEvent
from commanderbot.ext.automod.guards import FlagsGuard, RolesGuard
from commanderbot.ext.automod.types import AutomodRuleRef
from commanderbot.ext.automod.trigger import AutomodTrigger

__all__ = ("MemberLostFlags",)


class MemberLostFlags(AutomodTrigger):
    """
    Triggers when a `discord.Member` loses certain flags.
    """

    type: Literal["member_lost_flags"] = "member_lost_flags"
    event_types = (events.MemberUpdated,)

    flags: Optional[FlagsGuard] = None
    """The flags to match against. If empty, all flags will match."""

    roles: Optional[RolesGuard] = None
    """The roles to match against. If empty, all roles will match."""

    @override
    async def ignore(self, rule: AutomodRuleRef, event: AutomodEvent) -> bool:
        assert isinstance(event, events.MemberUpdated)

        if self.flags and not self.flags.lost_any(event.before, event.after):
            return True

        before_flags = event.before.flags.value
        after_flags = event.after.flags.value
        before_public_flags = event.before.public_flags.value
        after_public_flags = event.after.public_flags.value
        if before_flags <= after_flags and before_public_flags <= after_public_flags:
            return True

        if self.roles and self.roles.ignore(event.member):
            return True

        return False
