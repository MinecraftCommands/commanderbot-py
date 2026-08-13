from typing import TYPE_CHECKING, override

from discord import (
    ChannelType,
    Interaction,
    SelectDefaultValue,
    SelectDefaultValueType,
    TextStyle,
    ui,
)

from commanderbot.ext.automod.automod_exceptions import (
    CouldNotValidateModifiedLogChannel,
)
from commanderbot.ext.automod.automod_store import AutomodStore
from commanderbot.lib.cogs.views import CogStateModal
from commanderbot.lib.log_channel import LogChannel

__all__ = ("ModifyDefaultLogModal",)

if TYPE_CHECKING:
    from commanderbot.ext.automod.automod_guild_state import AutomodGuildState


class ModifyDefaultLogModal(CogStateModal["AutomodGuildState", AutomodStore]):
    def __init__(
        self, interaction: Interaction, state: AutomodGuildState, log: LogChannel
    ):
        super().__init__(
            interaction,
            state,
            title="Modifying default log channel",
            custom_id="commanderbot_ext:automod.log.modify",
        )

        self.channel_input = ui.ChannelSelect(
            channel_types=[ChannelType.text, ChannelType.public_thread],
            placeholder="Pick a channel",
            default_values=[
                SelectDefaultValue(id=log.channel, type=SelectDefaultValueType.channel)
            ],
            min_values=1,
            max_values=1,
            required=True,
        )
        self.channel_label = ui.Label(
            text="The channel to send log messages in", component=self.channel_input
        )

        self.emoji_input = ui.TextInput(
            style=TextStyle.short,
            placeholder="Ex: 🔥",
            default=log.emoji or "",
            required=False,
        )
        self.emoji_label = ui.Label(
            text="The emoji used for log messages",
            description="Can be a regular emoji or Discord emoji",
            component=self.emoji_input,
        )

        self.color_input = ui.TextInput(
            style=TextStyle.short,
            placeholder="Ex: 'mcc_blue' or '0x00ACED'",
            default=str(log.color) if log.color is not None else "",
            required=False,
        )
        self.color_label = ui.Label(
            text="The color used for log messages",
            description="Can be the name of a color, a hex code, or an integer",
            component=self.color_input,
        )

        self.stacktrace_input = ui.CheckboxGroup(required=False)
        self.stacktrace_input.add_option(
            label="\u200b", default=log.stacktrace or False
        )
        self.stacktrace_label = ui.Label(
            text="Print exception stacktraces", component=self.stacktrace_input
        )

        self.allowed_mentions_input = ui.CheckboxGroup(required=False)
        self.allowed_mentions_input.add_option(
            label="Everyone", default=bool(log.allowed_mentions.everyone)
        )
        self.allowed_mentions_input.add_option(
            label="Users", default=bool(log.allowed_mentions.users)
        )
        self.allowed_mentions_input.add_option(
            label="Roles", default=bool(log.allowed_mentions.roles)
        )
        self.allowed_mentions_input.add_option(
            label="Replied User", default=bool(log.allowed_mentions.replied_user)
        )
        self.allowed_mentions_label = ui.Label(
            text="The types of mentions allowed in log messages",
            component=self.allowed_mentions_input,
        )

        self.add_item(self.channel_label)
        self.add_item(self.emoji_label)
        self.add_item(self.color_label)
        self.add_item(self.stacktrace_label)
        self.add_item(self.allowed_mentions_label)

    @override
    async def on_submit(self, interaction: Interaction):
        raw_log = {
            "channel": self.channel_input.values[-1].id,
            "emoji": self.emoji_input.value or None,
            "color": self.color_input.value or None,
            "stacktrace": bool(self.stacktrace_input.values) or None,
            "allowed_mentions": {
                "everyone": "Everyone" in self.allowed_mentions_input.values,
                "users": "Users" in self.allowed_mentions_input.values,
                "roles": "Roles" in self.allowed_mentions_input.values,
                "replied_user": "Replied User" in self.allowed_mentions_input.values,
            },
        }

        try:
            log = LogChannel.model_validate(raw_log)
            await self.store.modify_default_log(self.state.guild, log)
            await interaction.response.send_message(
                f"Modified default log channel <#{log.channel}>"
            )
        except ValueError as ex:
            raise CouldNotValidateModifiedLogChannel(ex)
