from typing import Literal, Optional, override

from discord import Thread
from pydantic import Field

from commanderbot.ext.automod.action import AutomodAction
from commanderbot.ext.automod.automod_context import AutomodContext
from commanderbot.lib.allowed_mentions import AllowedMentions
from commanderbot.lib.predicates import is_messagable_guild_channel, is_thread
from commanderbot.lib.timedelta import Timedelta
from commanderbot.lib.types import ChannelID, MessageableGuildChannel
from commanderbot.lib.utils import dict_without_nones

__all__ = ("SendMessage",)


class SendMessage(AutomodAction):
    """
    Send a message.
    """

    type: Literal["send_message"]

    content: str
    """The content of the message to send."""

    channel: Optional[ChannelID] = None
    """The channel to send the message in. Defaults to the channel in context."""

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

    def _resolve_channel(
        self, context: AutomodContext
    ) -> Optional[MessageableGuildChannel | Thread]:
        channel = context.event.channel
        if self.channel:
            channel = context.bot.get_channel(self.channel)

        if is_messagable_guild_channel(channel) or is_thread(channel):
            return channel

    @override
    async def apply(self, context: AutomodContext):
        channel = self._resolve_channel(context)
        if not channel:
            return

        content = context.format_content(self.content)
        params = dict_without_nones(
            allowed_mentions=self.allowed_mentions,
            delete_after=td.total_seconds() if (td := self.delete_after) else None,
            suppress_embeds=self.suppress_embeds,
            silent=self.silent,
        )
        await channel.send(content, **params)
