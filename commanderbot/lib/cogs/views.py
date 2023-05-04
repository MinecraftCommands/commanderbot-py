from typing import Generic, Optional, TypeVar

from discord import Interaction
from discord.ext.commands import Bot, Cog
from discord.ui import Modal

__all__ = ("CogStateModal",)

CogStateType = TypeVar("CogStateType")
CogStoreType = TypeVar("CogStoreType")


class CogStateModal(Generic[CogStateType, CogStoreType], Modal):
    """
    A base class for modals that can access a cog state.

    By default, interactions will be checked against `original_interaction`
    and errors will be piped through the command tree's error handler.

    Attributes
    -----------
    bot
        The bot/client instance the cog is attached to.
    cog
        The cog instance this state is attached to.
    state
        The cog state this modal is attached to.
    store
        The data storage for this cog.
    original_interaction
        The interaction that sent this modal.
    modal_interaction
        The interaction that's sent when the modal is submitted.
    """

    def __init__(
        self,
        interaction: Interaction,
        state: CogStateType,
        *,
        title: str,
        custom_id: str,
        timeout: Optional[float] = None,
    ):
        self.original_interaction: Interaction = interaction
        self.modal_interaction: Optional[Interaction] = None

        self.state: CogStateType = state
        self.bot: Bot = getattr(state, "bot")
        self.cog: Cog = getattr(state, "cog")
        self.store: CogStoreType = getattr(state, "store")

        super().__init__(title=title, custom_id=custom_id, timeout=timeout)

    async def interaction_check(self, interaction: Interaction) -> bool:
        # Check if the same user sent this interaction and the original interaction
        return self.original_interaction.user == interaction.user

    async def on_error(self, interaction: Interaction, error: Exception):
        # Pipe this error through the command tree's error handler
        await self.bot.tree.on_error(interaction, error)  # type: ignore
