from typing import Literal, Optional, override

from pydantic import Field

from commanderbot.ext.automod.action import AutomodAction
from commanderbot.ext.automod.automod_context import AutomodContext
from commanderbot.lib.allowed_mentions import AllowedMentions
from commanderbot.lib.timedelta import Timedelta
from commanderbot.lib.utils import dict_without_nones

__all__ = ("DMMember",)


class DMMember(AutomodAction):
    """
    Send a direct message to the member in context.
    """

    type: Literal["dm_member"]

    content: str
    """The content of the message to send."""

    allowed_mentions: AllowedMentions = Field(
        default_factory=AllowedMentions.not_everyone
    )
    """
    The types of mentions allowed in the message. Unless otherwise specified, only
    "everyone" mentions will be suppressed.
    """

    delete_after: Optional[Timedelta] = None
    """The amount of time to wait before deleting the message, if at all."""

    suppress_embeds: Optional[bool] = None
    """Suppress any embeds for the message, if at all."""

    silent: Optional[bool] = None
    """Suppress desktop and push notifications for the message, if at all."""

    @override
    async def apply(self, context: AutomodContext):
        if member := context.event.member:
            content = context.format_content(self.content)
            params = dict_without_nones(
                allowed_mentions=self.allowed_mentions,
                delete_after=td.total_seconds() if (td := self.delete_after) else None,
                suppress_embeds=self.suppress_embeds,
                silent=self.silent,
            )
            await member.send(content, **params)
