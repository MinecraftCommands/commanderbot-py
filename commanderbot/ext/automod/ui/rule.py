from typing import TYPE_CHECKING, override

from discord import Interaction, TextStyle, ui
from discord.utils import format_dt

from commanderbot.ext.automod.automod_exceptions import (
    CouldNotValidateModifiedAutomodRule,
    CouldNotValidateNewAutomodRule,
)
from commanderbot.ext.automod.automod_store import AutomodStore
from commanderbot.ext.automod.rule import AutomodRule, AutomodRuleMetadata
from commanderbot.lib.cogs.views import CogStateModal
from commanderbot.lib.constants import MAX_MODAL_TITLE_LENGTH

__all__ = (
    "AddRuleModal",
    "ModifyRuleModal",
    "RuleDetails",
    "RuleList",
)

if TYPE_CHECKING:
    from commanderbot.ext.automod.automod_guild_state import AutomodGuildState


class AddRuleModal(CogStateModal["AutomodGuildState", AutomodStore]):
    def __init__(self, interaction: Interaction, state: AutomodGuildState):
        super().__init__(interaction, state, title="Add a new rule")

        self.rule_input = ui.TextInput(
            style=TextStyle.paragraph,
            placeholder="{}",
            required=True,
        )
        self.rule_label = ui.Label(
            text="The rule in Json format",
            component=self.rule_input,
        )

        self.rule_schema_help = ui.TextDisplay(
            f"-# Run {state.get_schema_command()} if you need the schema"
        )

        self.add_item(self.rule_label)
        self.add_item(self.rule_schema_help)

    @override
    async def on_submit(self, interaction: Interaction):
        try:
            rule = AutomodRule.model_validate_json(self.rule_input.value)
            await self.store.add_rule(self.guild, rule, interaction.user.id)
            await interaction.response.send_message(f"Added rule `{rule.name}`")
        except ValueError as ex:
            raise CouldNotValidateNewAutomodRule(ex)


class ModifyRuleModal(CogStateModal["AutomodGuildState", AutomodStore]):
    def __init__(
        self, interaction: Interaction, state: AutomodGuildState, rule: AutomodRule
    ):
        title: str = f"Modifying rule '{rule.name}'"
        if len(title) > MAX_MODAL_TITLE_LENGTH:
            title = f"{title[:42]}..."

        super().__init__(interaction, state, title=title)

        self.rule_input = ui.TextInput(
            style=TextStyle.paragraph,
            placeholder="{}",
            default=rule.model_dump_json(indent=4, exclude_defaults=True),
            required=True,
        )
        self.rule_label = ui.Label(
            text="The rule in Json format",
            component=self.rule_input,
        )

        self.rule_schema_help = ui.TextDisplay(
            f"-# Run {state.get_schema_command()} if you need the schema"
        )

        self.add_item(self.rule_label)
        self.add_item(self.rule_schema_help)

    @override
    async def on_submit(self, interaction: Interaction):
        try:
            rule = AutomodRule.model_validate_json(self.rule_input.value)
            await self.store.modify_rule(self.guild, rule, interaction.user.id)
            await interaction.response.send_message(f"Modified rule `{rule.name}`")
        except ValueError as ex:
            raise CouldNotValidateModifiedAutomodRule(ex)


class RuleDetails(ui.LayoutView):
    def __init__(self, rule: AutomodRule, metadata: AutomodRuleMetadata):
        super().__init__()

        container = ui.Container(accent_color=0x00ACED)
        self.add_item(container)

        container.add_item(ui.TextDisplay(f"### 📜 Details for rule `{rule.name}`"))
        container.add_item(ui.Separator())

        container.add_item(ui.File(f"attachment://{rule.name}.json"))
        container.add_item(ui.Separator())

        description: str = f"`{rule.description}`" if rule.description else "**None!**"
        fields: dict[str, str] = {
            "Name": f"`{rule.name}`",
            "Description": description,
            "Enabled": "❌" if rule.disabled else "✅",
            "Hits": f"`{metadata.hits}`",
            "Added by": f"<@{metadata.added_by_id}>({format_dt(metadata.added_on, style='R')})",
            "Modified by": f"<@{metadata.modified_by_id}>({format_dt(metadata.modified_on, style='R')})",
        }

        for field_name, field_value in fields.items():
            container.add_item(ui.TextDisplay(f"**{field_name}**: {field_value}"))


class RuleList(ui.LayoutView):
    def __init__(self, rules: list[AutomodRule]):
        super().__init__()

        container = ui.Container(accent_color=0x00ACED)
        self.add_item(container)

        container.add_item(ui.TextDisplay("### 📜 All rules"))
        container.add_item(ui.Separator())

        formatted_rules: list[str] = []
        enabled_rules: int = 0
        disabled_rules: int = 0
        for rule in rules:
            if not rule.disabled:
                formatted_rules.append(rule.name)
                enabled_rules += 1
            else:
                formatted_rules.append(f"{rule.name} (Disabled)")
                disabled_rules += 1

        if formatted_rules:
            lines = "\n".join(("```", "\n".join(formatted_rules), "```"))
            container.add_item(ui.TextDisplay(lines))
        else:
            container.add_item(ui.TextDisplay("**None!**"))

        container.add_item(ui.Separator())
        container.add_item(
            ui.TextDisplay(f"-# Enabled: {enabled_rules} | Disabled: {disabled_rules}")
        )
