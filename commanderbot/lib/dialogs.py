import asyncio
from enum import Enum
from typing import Optional

import discord
from discord import ButtonStyle, Interaction, Member, Message, Reaction
from discord.ext.commands import Bot, Context
from discord.interactions import Interaction
from discord.ui import Button, View, button

from commanderbot.lib.allowed_mentions import AllowedMentions

__all__ = (
    "ConfirmationResult",
    "confirm_with_reaction",
    "ConfirmView",
    "respond_with_confirmation",
)


class ConfirmationResult(Enum):
    YES = "yes"
    NO = "no"
    NO_RESPONSE = "timeout"


async def confirm_with_reaction(
    bot: Bot,
    ctx: Context,
    content: str,
    timeout: float = 60.0,
    reaction_yes: str = "✅",
    reaction_no: str = "❌",
) -> ConfirmationResult:
    """
    Ask a user to confirm an action via emoji reaction.

    The `bot` will send a reply to the message contained within `ctx`, composed of the
    given `content`. It wait for up to `timeout` seconds for a "yes" or "no" response,
    in the form of an emoji reaction. If no response is received, the answer "no" will
    be assumed.
    """

    # Build and send a confirmation message.
    conf_message: Message = await ctx.message.reply(
        content,
        allowed_mentions=AllowedMentions.only_replies(),
    )

    # Have the bot pre-fill the possible choices for convenience.
    await conf_message.add_reaction(reaction_yes)
    await conf_message.add_reaction(reaction_no)

    # Define a callback to listen for a reaction to the confirmation message.
    def reacted_to_conf_message(reaction: Reaction, user: Member):
        return (
            reaction.message == conf_message
            and user == ctx.author
            and str(reaction.emoji) in (reaction_yes, reaction_no)
        )

    # Attempt to wait for a reaction to the confirmation message.
    try:
        conf_reaction, _ = await bot.wait_for(
            "reaction_add", timeout=timeout, check=reacted_to_conf_message
        )

    # If an appropriate reaction is not received soon enough, assume "no."
    except asyncio.TimeoutError:
        await conf_message.remove_reaction(reaction_yes, bot.user)  # type: ignore
        await conf_message.remove_reaction(reaction_no, bot.user)  # type: ignore
        return ConfirmationResult.NO_RESPONSE

    # Otherwise, check which reaction was applied.
    else:
        assert isinstance(conf_reaction, Reaction)
        # Check if the response is a "yes."
        if str(conf_reaction.emoji) == reaction_yes:
            await conf_message.remove_reaction(reaction_no, bot.user)  # type: ignore
            return ConfirmationResult.YES

    # If we get this far, the answer is an explicit "no."
    await conf_message.remove_reaction(reaction_yes, bot.user)  # type: ignore
    return ConfirmationResult.NO


class ConfirmView(View):
    def __init__(self, interaction: Interaction, timeout: Optional[float] = None):
        self.original_interaction: Interaction = interaction
        self.result = ConfirmationResult.NO_RESPONSE
        super().__init__(timeout=timeout)

    # @overrides View
    async def interaction_check(self, interaction: Interaction) -> bool:
        if interaction.user != self.original_interaction.user:
            await interaction.response.send_message(
                "😠 This confirmation dialog isn't for you", ephemeral=True
            )
            return False
        return True

    # @overrides View
    async def on_timeout(self):
        # Disable all buttons and set their color to gray
        for button in self.children:
            assert isinstance(button, Button)
            button.style = ButtonStyle.gray
            button.disabled = True

        # Attempt to edit the view (The original response may have been deleted)
        try:
            await self.original_interaction.edit_original_response(view=self)
        except:
            pass

    @button(
        label="Yes",
        style=ButtonStyle.green,
        custom_id="commanderbot_lib:dialogs.confirm_view.yes",
    )
    async def yes_callback(self, interaction: Interaction, button: Button):
        self.result = ConfirmationResult.YES
        await self._on_confirm(interaction, button)

    @button(
        label="No",
        style=ButtonStyle.red,
        custom_id="commanderbot_lib:dialogs.confirm_view.no",
    )
    async def no_callback(self, interaction: Interaction, button: Button):
        self.result = ConfirmationResult.NO
        await self._on_confirm(interaction, button)

    async def _on_confirm(self, interaction: Interaction, pressed_button: Button):
        # Remove all buttons except for the one that was interacted with
        for button in self.children[:]:
            assert isinstance(button, Button)
            if button is not pressed_button:
                self.remove_item(button)

        # Disable the button that was interacted with
        pressed_button.disabled = True

        # Attempt to edit the view (The original response may have been deleted)
        try:
            await interaction.response.edit_message(view=self)
        except:
            pass

        # Stop accepting inputs
        self.stop()


async def respond_with_confirmation(
    interaction: Interaction,
    content: str,
    *,
    timeout: float = 60.0,
    ephemeral=False,
    allowed_mentions: discord.AllowedMentions = discord.AllowedMentions.none()
) -> ConfirmationResult:
    """
    Ask a user to confirm an action via a `discord.ui.View` with buttons.

    The `content` and confirmation view will be sent as a response to `interaction`.
    The view will wait for up to `timeout` seconds for a "yes" or "no" response.
    If no response is received, "no response" will be returned.
    """

    # Create the view and send it as a response
    view = ConfirmView(interaction, timeout)
    await interaction.response.send_message(
        content, view=view, ephemeral=ephemeral, allowed_mentions=allowed_mentions
    )

    # Wait for the view to be interacted with or time out then return the result
    await view.wait()
    return view.result
