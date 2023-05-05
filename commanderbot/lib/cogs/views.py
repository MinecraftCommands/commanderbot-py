from typing import Any, Generic, Optional, TypeVar

from discord import Interaction
from discord.ext.commands import Bot, Cog
from discord.interactions import Interaction
from discord.ui import Modal, View
from discord.ui.item import Item

__all__ = ("CogStateModal", "CogStateView")

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

    # @overrides View
    async def interaction_check(self, interaction: Interaction) -> bool:
        # Check if this interaction and the original interaction are from the same user
        return interaction.user == self.original_interaction.user

    # @overrides Modal
    async def on_error(self, interaction: Interaction, error: Exception):
        # Pipe this error through the command tree's error handler
        await self.bot.tree.on_error(interaction, error)  # type: ignore


class CogStateView(Generic[CogStateType, CogStoreType], View):
    """
    A base class for views that can access a cog state.

    By default, interactions will be checked against `original_interaction`
    and errors will be piped through the command tree's error handler.

    Attributes
    -----------
    bot
        The bot/client instance the cog is attached to.
    cog
        The cog instance this state is attached to.
    state
        The cog state this view is attached to.
    store
        The data storage for this cog.
    original_interaction
        The interaction that sent this view.
    view_interaction
        The interaction that's sent when the view is interacted with.
    """

    def __init__(
        self,
        interaction: Interaction,
        state: CogStateType,
        *,
        timeout: Optional[float] = None,
    ):
        self.original_interaction: Interaction = interaction
        self.view_interaction: Optional[Interaction] = None

        self.state: CogStateType = state
        self.bot: Bot = getattr(state, "bot")
        self.cog: Cog = getattr(state, "cog")
        self.store: CogStateType = getattr(state, "store")

        super().__init__(timeout=timeout)

    # @overrides View
    async def interaction_check(self, interaction: Interaction) -> bool:
        # Check if this interaction and the original interaction are from the same user
        return interaction.user == self.original_interaction.user

    # @overrides View
    async def on_error(self, interaction: Interaction, error: Exception, item: Item):
        # Pipe this error through the command tree's error handler
        await self.bot.tree.on_error(interaction, error)  # type: ignore
