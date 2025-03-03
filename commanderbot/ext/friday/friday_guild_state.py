from dataclasses import dataclass

from discord import Interaction

from commanderbot.ext.friday.friday_store import FridayStore
from commanderbot.lib.cogs import CogGuildState
from commanderbot.lib.cogs.views import CogStateModal
from commanderbot.lib import ChannelID


@dataclass
class FridayGuildState(CogGuildState):
    """
    Encapsulates the state and logic of the faq cog, at the guild level.

    Attributes
    -----------
    store
        The store used to interface with persistent data in a database-agnostic way.
    """

    store: FridayStore

    async def register_channel(self, interaction: Interaction, channel_id: ChannelID):
        await self.store.register_channel(self.guild, channel_id)
        await interaction.response.send_message(f"Registered <#{channel_id}>")

    async def unregister_channel(self, interaction: Interaction, channel_id: ChannelID):
        await self.store.unregister_channel(self.guild, channel_id)
        await interaction.response.send_message(f"Unregistered <#{channel_id}>")

    async def add_rule(self, interaction: Interaction):
        pass

    async def modify_rule(self, interaction: Interaction, name: str):
        pass

    async def remove_rule(self, interaction: Interaction, name: str):
        pass

    async def show_rule_details(self, interaction: Interaction, name: str):
        pass

    async def list_rules(self, interaction: Interaction):
        pass
