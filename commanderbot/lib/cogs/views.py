from typing import Generic, Optional, TypeVar, override

from discord import Guild, Interaction, ui
from discord.ext.commands import Bot, Cog

from commanderbot.lib.utils import dict_without_nones

__all__ = ("CogStateModal", "CogStateView")

CogStateType = TypeVar("CogStateType")
CogStoreType = TypeVar("CogStoreType")


class CogStateModal(Generic[CogStateType, CogStoreType], ui.Modal):  # noqa: PYI059, UP046 - Discord.py has issues with the newer generic syntax
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
        custom_id: Optional[str] = None,
        timeout: Optional[float] = None,
    ):
        self.original_interaction: Interaction = interaction
        self.modal_interaction: Optional[Interaction] = None

        self.state: CogStateType = state
        self.bot: Bot = getattr(state, "bot")
        self.cog: Cog = getattr(state, "cog")
        self.guild: Guild = getattr(state, "guild")
        self.store: CogStoreType = getattr(state, "store")

        params = dict_without_nones(
            title=title,
            custom_id=custom_id,
            timeout=timeout,
        )
        super().__init__(**params)

    @override
    async def interaction_check(self, interaction: Interaction) -> bool:
        # Check if this interaction and the original interaction are from the same user
        return interaction.user == self.original_interaction.user

    @override
    async def on_error(self, interaction: Interaction, error: Exception):
        # Pipe this error through the command tree's error handler
        await self.bot.tree.on_error(interaction, error)  # type: ignore[ty:missing-argument, ty:invalid-argument-type] - Maybe fix this in the future? #enhance


class CogStateView(Generic[CogStateType, CogStoreType], ui.View):  # noqa: PYI059, UP046 - Discord.py has issues with the newer generic syntax
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
        self.guild: Guild = getattr(state, "guild")
        self.store: CogStateType = getattr(state, "store")

        super().__init__(timeout=timeout)

    @override
    async def interaction_check(self, interaction: Interaction) -> bool:
        # Check if this interaction and the original interaction are from the same user
        return interaction.user == self.original_interaction.user

    @override
    async def on_error(self, interaction: Interaction, error: Exception, item: ui.Item):
        # Pipe this error through the command tree's error handler
        await self.bot.tree.on_error(interaction, error)  # type: ignore[ty:missing-argument, ty:invalid-argument-type] - Maybe fix this in the future? #enhance
