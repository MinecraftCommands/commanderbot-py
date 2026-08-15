from typing import Literal, Optional, override

from pydantic import Field

from commanderbot.ext.automod.action import AutomodAction
from commanderbot.ext.automod.automod_context import AutomodContext
from commanderbot.lib.allowed_mentions import AllowedMentions
from commanderbot.lib.timedelta import Timedelta
from commanderbot.lib.utils import dict_without_nones

__all__ = ("ReplyToMessage",)


class ReplyToMessage(AutomodAction):
    """
    Reply to the message in context.
    """

    type: Literal["reply_to_message"]

    content: str
    """The content of the message to send."""

    mention_author: Optional[bool] = None
    """Mention the author of the message being replied to, if at all."""

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
        if message := context.event.message:
            content = context.format_content(self.content)
            params = dict_without_nones(
                mention_author=self.mention_author,
                allowed_mentions=self.allowed_mentions,
                delete_after=td.total_seconds() if (td := self.delete_after) else None,
                suppress_embeds=self.suppress_embeds,
                silent=self.silent,
            )
            await message.reply(content, **params)
