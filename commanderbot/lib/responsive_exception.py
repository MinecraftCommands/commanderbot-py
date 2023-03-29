import datetime
from typing import Optional, Union

from discord import (
    AllowedMentions,
    Interaction,
    InteractionMessage,
    InteractionResponseType,
    WebhookMessage,
)
from discord.ext.commands import Context

from commanderbot.lib.utils.datetimes import datetime_to_int
from commanderbot.lib.utils.utils import utcnow_aware

__all__ = ("ResponsiveException",)


class ResponsiveException(Exception):
    def __init__(
        self,
        *args,
        allowed_mentions: Optional[AllowedMentions] = None,
    ):
        self.allowed_mentions: Optional[AllowedMentions] = allowed_mentions
        super().__init__(*args)

    @classmethod
    def allowed_mentions_default_factory(cls) -> AllowedMentions:
        return AllowedMentions.none()

    async def respond(
        self,
        context: Union[Context, Interaction],
        allowed_mentions: Optional[AllowedMentions] = None,
    ):
        allowed_mentions = (
            allowed_mentions
            or self.allowed_mentions
            or self.allowed_mentions_default_factory()
        )

        # Handle command errors
        if isinstance(context, Context):
            await context.message.reply(str(self), allowed_mentions=allowed_mentions)
            return

        # Handle app command errors that haven't had their interaction responded to
        if not context.response.is_done():
            await context.response.send_message(
                str(self), allowed_mentions=allowed_mentions, ephemeral=True
            )
            return

        # Handle app command errors that had their interaction responded to without a defer
        if context.response.type not in {
            InteractionResponseType.deferred_channel_message,
            InteractionResponseType.deferred_message_update,
        }:
            await context.followup.send(
                str(self), allowed_mentions=allowed_mentions, ephemeral=True
            )
            return

        # Handle app command errors that had their interaction deferred
        original_response: InteractionMessage = await context.original_response()
        if original_response.flags.ephemeral:
            # Handle ephemeral defers by just sending an ephemeral followup
            await context.followup.send(
                str(self), allowed_mentions=allowed_mentions, ephemeral=True
            )
        else:
            # Handle regular defers by sending a followup that everyone can see
            # The followup will be deleted after a small delay
            deleting_in_ts: int = datetime_to_int(
                utcnow_aware() + datetime.timedelta(seconds=11)
            )
            deleting_in_msg: str = (
                f"(*This message will self destruct in <t:{deleting_in_ts}:R>*)"
            )
            message: WebhookMessage = await context.followup.send(
                f"{self}\n{deleting_in_msg}",
                allowed_mentions=allowed_mentions,
                wait=True,
            )
            
            try:
                await message.delete(delay=10)
            except:
                pass
