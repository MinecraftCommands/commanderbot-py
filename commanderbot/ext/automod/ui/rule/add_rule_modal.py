from typing import TYPE_CHECKING, override

from discord import Interaction, TextStyle, ui

from commanderbot.ext.automod.automod_exceptions import CouldNotValidateNewAutomodRule
from commanderbot.ext.automod.automod_store import AutomodStore
from commanderbot.ext.automod.rule import AutomodRule
from commanderbot.lib.cogs.views import CogStateModal

__all__ = ("AddRuleModal",)

if TYPE_CHECKING:
    from commanderbot.ext.automod.automod_guild_state import AutomodGuildState


class AddRuleModal(CogStateModal["AutomodGuildState", AutomodStore]):
    def __init__(self, interaction: Interaction, state: AutomodGuildState):
        super().__init__(
            interaction,
            state,
            title="Add a new rule",
            custom_id="commanderbot_ext:automod.rule.add",
        )

        self.rule_input = ui.TextInput(
            style=TextStyle.paragraph,
            placeholder="{}",
            required=True,
        )
        self.rule_input_label = ui.Label(
            text="The rule in Json format",
            description=f"Run {state.get_schema_command()} if you need the schema",
            component=self.rule_input,
        )
        self.add_item(self.rule_input_label)

    @override
    async def on_submit(self, interaction: Interaction):
        try:
            rule = AutomodRule.model_validate_json(self.rule_input.value)
            await self.store.add_rule(self.state.guild, rule, interaction.user.id)
            await interaction.response.send_message(f"Added rule `{rule.name}`")
        except ValueError as ex:
            raise CouldNotValidateNewAutomodRule(ex)
