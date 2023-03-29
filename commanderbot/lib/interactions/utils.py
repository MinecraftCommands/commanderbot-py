from typing import Optional

from discord import AllowedMentions, Interaction, InteractionResponseType

__all__ = ("send_or_followup", "command_name", "is_deferred")


async def send_or_followup(
    interaction: Interaction,
    content,
    *,
    allowed_mentions: Optional[AllowedMentions] = None,
    ephemeral=False
):
    """
    Respond to an interaction using `Interaction.response.send_message()`.
    If that has already happened, it sends a followup message using `Interaction.interaction.followup.send` instead.
    """
    mentions: AllowedMentions = allowed_mentions or AllowedMentions.none()
    if not interaction.response.is_done():
        await interaction.response.send_message(
            content,
            allowed_mentions=mentions,
            ephemeral=ephemeral,
        )
    else:
        await interaction.followup.send(
            content,
            allowed_mentions=mentions,
            ephemeral=ephemeral,
        )


def command_name(interaction: Interaction) -> Optional[str]:
    """
    Returns the fully qualified command name.
    """
    if interaction.command:
        return interaction.command.qualified_name


def is_deferred(interaction: Interaction) -> bool:
    """
    Returns `True` if the interaction response was deferred.
    """
    return interaction.response.type in {
        InteractionResponseType.deferred_channel_message,
        InteractionResponseType.deferred_message_update,
    }
