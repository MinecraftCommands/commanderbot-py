from typing import TYPE_CHECKING, override

from discord import Interaction, TextStyle, ui

from commanderbot.ext.automod import buckets
from commanderbot.ext.automod.automod_exceptions import (
    CouldNotValidateNewFlaggedImageAttachmentsBucket,
)
from commanderbot.ext.automod.automod_store import AutomodStore
from commanderbot.lib.cogs.views import CogStateModal
from commanderbot.lib.constants import MAX_MODAL_TITLE_LENGTH
from commanderbot.lib.timedelta import TimedeltaAdapter

__all__ = (
    "AddFlaggedImageAttachmentsBucket",
    "FlaggedImageAttachmentsBucketDetails",
    "ModifyFlaggedImageAttachmentsBucket",
)
if TYPE_CHECKING:
    from commanderbot.ext.automod.automod_guild_state import AutomodGuildState


class AddFlaggedImageAttachmentsBucket(
    CogStateModal["AutomodGuildState", AutomodStore]
):
    def __init__(self, interaction: Interaction, state: AutomodGuildState):
        super().__init__(
            interaction, state, title="Add a new flagged image attachments bucket"
        )

        self.name_input = ui.TextInput(
            style=TextStyle.short,
            placeholder="Ex: 'sample-text'",
            required=True,
        )
        self.name_label = ui.Label(
            text="The name of the bucket", component=self.name_input
        )

        self.description_input = ui.TextInput(
            style=TextStyle.short,
            placeholder="Ex: 'Spam'",
            required=False,
        )
        self.description_label = ui.Label(
            text="Describe what the bucket is for", component=self.description_input
        )

        self.lifetime_input = ui.TextInput(
            style=TextStyle.short,
            placeholder="Ex: 'PT5H30M', '2 days, 05:15:00', or '1.5'",
            required=True,
        )
        self.lifetime_label = ui.Label(
            text="How long to store flagged image attachments",
            description="Longer durations are able to store more image attachments, but take more memory on average",
            component=self.lifetime_input,
        )

        self.add_item(self.name_label)
        self.add_item(self.description_label)
        self.add_item(self.lifetime_label)

    @override
    async def on_submit(self, interaction: Interaction):
        raw_bucket: dict = {
            "type": "flagged_image_attachments",
            "name": self.name_input.value,
            "description": self.description_input.value or None,
            "lifetime": self.lifetime_input.value,
        }

        try:
            bucket = buckets.FlaggedImageAttachments.model_validate(raw_bucket)
            await self.store.add_bucket(self.guild, bucket)
            await interaction.response.send_message(
                f"Added flagged image attachments bucket `{bucket.name}`"
            )
        except ValueError as ex:
            raise CouldNotValidateNewFlaggedImageAttachmentsBucket(ex)


class ModifyFlaggedImageAttachmentsBucket(
    CogStateModal["AutomodGuildState", AutomodStore]
):
    def __init__(
        self,
        interaction: Interaction,
        state: AutomodGuildState,
        bucket: buckets.FlaggedImageAttachments,
    ):
        self.name: str = bucket.name
        title: str = f"Modifying bucket '{bucket.name}'"
        if len(title) > MAX_MODAL_TITLE_LENGTH:
            title = f"{title[:42]}..."

        super().__init__(interaction, state, title=title)

        self.description_input = ui.TextInput(
            style=TextStyle.short,
            placeholder="Ex: 'Spam'",
            default=bucket.description or "",
            required=False,
        )
        self.description_label = ui.Label(
            text="Describe what the bucket is for", component=self.description_input
        )

        lifetime: str = TimedeltaAdapter.dump_json(bucket.lifetime).decode().strip('"')
        self.lifetime_input = ui.TextInput(
            style=TextStyle.short,
            placeholder="Ex: 'PT5H30M', '2 days, 05:15:00', or '1.5'",
            default=lifetime,
            required=True,
        )
        self.lifetime_label = ui.Label(
            text="How long to record message history",
            description="Longer durations are able to record more message history, but take more memory on average",
            component=self.lifetime_input,
        )

        self.add_item(self.description_label)
        self.add_item(self.lifetime_label)

    @override
    async def on_submit(self, interaction: Interaction):
        # The bucket needs to exist
        old_bucket = await self.store.require_bucket_with_type(
            self.guild, self.name, buckets.FlaggedImageAttachments
        )

        # Serialize the bucket and modify its data
        raw_bucket: dict = old_bucket.model_dump(exclude_defaults=True)
        raw_bucket["description"] = self.description_input.value or None
        raw_bucket["lifetime"] = self.lifetime_input.value

        try:
            # Deserialize the modified bucket and update the store
            bucket = buckets.FlaggedImageAttachments.model_validate(raw_bucket)
            await self.store.modify_bucket(self.guild, bucket)
            await interaction.response.send_message(
                f"Modified flagged image attachments bucket `{bucket.name}`"
            )
        except ValueError as ex:
            raise CouldNotValidateNewFlaggedImageAttachmentsBucket(ex)


class FlaggedImageAttachmentsBucketDetails(ui.LayoutView):
    def __init__(self, bucket: buckets.FlaggedImageAttachments):
        super().__init__()

        container = ui.Container(accent_color=0x00ACED)
        self.add_item(container)

        container.add_item(ui.TextDisplay(f"### 🪣 Details for bucket `{bucket.name}`"))
        container.add_item(ui.Separator())

        description: str = (
            f"`{bucket.description}`" if bucket.description else "**None!**"
        )
        lifetime: str = TimedeltaAdapter.dump_json(bucket.lifetime).decode().strip('"')
        fields: dict[str, str] = {
            "Type": f"`{bucket.type}`",
            "Name": f"`{bucket.name}`",
            "Description": description,
            "Enabled": "❌" if bucket.disabled else "✅",
            "Lifetime": f"`{lifetime}`",
            "Flagged": f"`{len(bucket.attachments)}`",
        }

        for field_name, field_value in fields.items():
            container.add_item(ui.TextDisplay(f"**{field_name}**: {field_value}"))
