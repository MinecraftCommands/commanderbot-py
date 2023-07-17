from typing import Optional, Union

from discord import AllowedMentions, Interaction
from discord.ext.commands import Context

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

        # Handle app command errors that had their interaction responded to
        await context.followup.send(
            str(self), allowed_mentions=allowed_mentions, ephemeral=True
        )
