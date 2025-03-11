import re
from dataclasses import dataclass
from typing import Optional

from discord import Interaction, Message, TextStyle
from discord.ui import TextInput

from commanderbot.ext.friday.friday_exceptions import (
    InvalidRuleChance,
    InvalidRuleCooldown,
)
from commanderbot.ext.friday.friday_store import FridayRule, FridayStore
from commanderbot.lib import (
    AllowedMentions,
    ChannelID,
    MessageableGuildChannel,
    constants,
    is_convertable_to,
    is_messagable_guild_channel,
    is_thread,
)
from commanderbot.lib.cogs import CogGuildState
from commanderbot.lib.cogs.views import CogStateModal


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

    async def _is_channel_registered(self, channel: MessageableGuildChannel):
        if is_thread(channel) and channel.parent:
            return await self.store.is_channel_registered(self.guild, channel.parent.id)
        return await self.store.is_channel_registered(self.guild, channel.id)

    async def on_message(self, message: Message):
        # Check if the channel the message was sent in was registered
        assert is_messagable_guild_channel(message.channel)
        if not await self._is_channel_registered(message.channel):
            return

        # If the channel was registered, check if the message content matches a rule
        rule = await self.store.check_rules(self.guild, message.clean_content)
        if not rule:
            return

        # Send the rule response to the channel the message was sent in
        await message.channel.send(
            rule.response, allowed_mentions=AllowedMentions.none()
        )

        # Update the rule's `last_response` and `hits`
        await self.store.update_on_rule_matched(rule)

    async def register_channel(self, interaction: Interaction, channel_id: ChannelID):
        await self.store.register_channel(self.guild, channel_id)
        await interaction.response.send_message(f"Registered <#{channel_id}>")

    async def unregister_channel(self, interaction: Interaction, channel_id: ChannelID):
        await self.store.unregister_channel(self.guild, channel_id)
        await interaction.response.send_message(f"Unregistered <#{channel_id}>")

    async def add_rule(self, interaction: Interaction):
        await interaction.response.send_modal(AddRuleModal(interaction, self))

    async def modify_rule(self, interaction: Interaction, name: str):
        rule: FridayRule = await self.store.require_rule(self.guild, name)
        await interaction.response.send_modal(ModifyRuleModal(interaction, self, rule))

    async def remove_rule(self, interaction: Interaction, name: str):
        pass

    async def show_rule_details(self, interaction: Interaction, name: str):
        pass

    async def list_rules(self, interaction: Interaction):
        pass


class FridayModal(CogStateModal[FridayGuildState, FridayStore]):
    """
    Base class for all friday modals.
    """

    @classmethod
    def pattern_to_str(cls, pattern: Optional[re.Pattern]) -> str:
        if pattern and pattern.pattern:
            return pattern.pattern
        return ""

    @classmethod
    def chance_from_str(cls, chance_str: str) -> float:
        if is_convertable_to(chance_str, float):
            chance = float(chance_str)
            if chance >= 0.0 and chance <= 1.0:
                return chance
        raise InvalidRuleChance(chance_str)

    @classmethod
    def cooldown_from_str(cls, cooldown_str: str) -> int:
        if is_convertable_to(cooldown_str, int):
            cooldown = int(cooldown_str)
            if cooldown >= 0:
                return cooldown
        raise InvalidRuleCooldown(cooldown_str)


class AddRuleModal(FridayModal):
    def __init__(self, interaction: Interaction, state: FridayGuildState):
        super().__init__(
            interaction,
            state,
            title="Add a new rule",
            custom_id="commanderbot_ext:friday.add",
        )

        self.name_field = TextInput(
            label="Name",
            style=TextStyle.short,
            placeholder="Ex: sample-text",
            required=True,
        )
        self.pattern_field = TextInput(
            label="Patten",
            style=TextStyle.short,
            placeholder="A regex pattern.",
            required=False,
        )
        self.chance_field = TextInput(
            label="Chance",
            style=TextStyle.short,
            placeholder="A floating point number between 0 and 1.",
            required=True,
        )
        self.cooldown_field = TextInput(
            label="Cooldown",
            style=TextStyle.short,
            placeholder="A cooldown amount in seconds.",
            required=True,
        )
        self.response_field = TextInput(
            label="Response",
            style=TextStyle.paragraph,
            placeholder="The response for this rule.",
            max_length=constants.MAX_MESSAGE_LENGTH,
            required=True,
        )

        self.add_item(self.name_field)
        self.add_item(self.pattern_field)
        self.add_item(self.chance_field)
        self.add_item(self.cooldown_field)
        self.add_item(self.response_field)

    async def on_submit(self, interaction: Interaction):
        rule: FridayRule = await self.store.add_rule(
            guild=self.state.guild,
            name=self.name_field.value,
            pattern=self.pattern_field.value or None,
            chance=self.chance_from_str(self.chance_field.value),
            cooldown=self.cooldown_from_str(self.cooldown_field.value),
            response=self.response_field.value,
            user_id=interaction.user.id,
        )
        await interaction.response.send_message(f"Added the rule `{rule.name}`")


class ModifyRuleModal(FridayModal):
    def __init__(
        self, interaction: Interaction, state: FridayGuildState, rule: FridayRule
    ):
        # Get the rule name and also limit the modal title to 45 characters
        self.rule_name: str = rule.name
        title: str = f"Modifying rule: {rule.name}"
        if len(title) > constants.MAX_MODAL_TITLE_LENGTH:
            title = f"{title[:42]}..."

        super().__init__(
            interaction, state, title=title, custom_id="commanderbot_ext:friday.modify"
        )

        self.pattern_field = TextInput(
            label="Patten",
            style=TextStyle.short,
            placeholder="A regex pattern.",
            default=self.pattern_to_str(rule.pattern),
            required=False,
        )
        self.chance_field = TextInput(
            label="Chance",
            style=TextStyle.short,
            placeholder="A floating point number between 0 and 1.",
            default=str(rule.chance),
            required=True,
        )
        self.cooldown_field = TextInput(
            label="Cooldown",
            style=TextStyle.short,
            placeholder="A cooldown amount in seconds.",
            default=str(rule.cooldown),
            required=True,
        )
        self.response_field = TextInput(
            label="Response",
            style=TextStyle.paragraph,
            placeholder="The response for this rule.",
            default=rule.response,
            max_length=constants.MAX_MESSAGE_LENGTH,
            required=True,
        )

        self.add_item(self.pattern_field)
        self.add_item(self.chance_field)
        self.add_item(self.cooldown_field)
        self.add_item(self.response_field)

    async def on_submit(self, interaction: Interaction):
        rule: FridayRule = await self.store.modify_rule(
            guild=self.state.guild,
            name=self.rule_name,
            pattern=self.pattern_field.value or None,
            chance=self.chance_from_str(self.chance_field.value),
            cooldown=self.cooldown_from_str(self.cooldown_field.value),
            response=self.response_field.value,
            user_id=interaction.user.id,
        )
        await interaction.response.send_message(f"Modified the rule `{rule.name}`")
