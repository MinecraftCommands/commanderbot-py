import asyncio
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import discord
from discord import (
    Attachment,
    Interaction,
    Member,
    Message,
    Reaction,
    Thread,
    ThreadMember,
    User,
    ui,
)
from discord.utils import format_dt
from mime_enum import MimeType

from commanderbot.core.utils import get_app_command
from commanderbot.ext.automod import buckets, events
from commanderbot.ext.automod.automod_context import AutomodContext
from commanderbot.ext.automod.automod_exceptions import (
    CouldNotValidateUploadedAutomodRule,
    UploadIsNotJsonFile,
)
from commanderbot.ext.automod.automod_store import AutomodStore
from commanderbot.ext.automod.event import AutomodEvent
from commanderbot.ext.automod.rule import AutomodRule
from commanderbot.ext.automod.ui import log as log_ui
from commanderbot.ext.automod.ui import rule as rule_ui
from commanderbot.lib.allowed_mentions import AllowedMentions
from commanderbot.lib.cogs import CogGuildState
from commanderbot.lib.dialogs import ConfirmationResult, respond_with_confirmation
from commanderbot.lib.types import GuildChannel, MessageableGuildChannel
from commanderbot.lib.utils import str_to_file


@dataclass
class AutomodGuildState(CogGuildState):
    """
    Encapsulates the state and logic of the automod cog, at the guild level.
    """

    store: AutomodStore

    # @@ COMMANDS

    async def set_default_log(self, interaction: Interaction):
        await interaction.response.send_modal(
            log_ui.SetDefaultLogModal(interaction, self)
        )

    async def modify_default_log(self, interaction: Interaction):
        log = await self.store.require_default_log(self.guild)
        await interaction.response.send_modal(
            log_ui.ModifyDefaultLogModal(interaction, self, log)
        )

    async def remove_default_log(self, interaction: Interaction):
        # Get the default log
        log = await self.store.require_default_log(self.guild)

        # Respond to this interaction with a confirmation dialog
        result: ConfirmationResult = await respond_with_confirmation(
            interaction,
            f"Are you sure you want to remove the default log channel <#{log.channel}>?",
            timeout=10.0,
        )

        # Handle response to dialog
        match result:
            case ConfirmationResult.YES:
                try:
                    await self.store.remove_default_log(self.guild)
                    await interaction.followup.send(
                        content=f"Removed the default log channel <#{log.channel}>"
                    )
                except Exception:
                    await interaction.delete_original_response()
                    raise
            case _:
                await interaction.followup.send(
                    f"Did not remove the default log channel <#{log.channel}>"
                )

    async def show_default_log_details(self, interaction: Interaction):
        # Get the default log
        log = await self.store.require_default_log(self.guild)

        # Create fields
        fields: dict[str, str] = {
            "Channel": f"<#{log.channel}>",
            "Emoji": log.emoji or "**None!**",
            "Color": f"`{log.color}`" if log.color is not None else "**None!**",
            "Stacktrace": "✅" if log.stacktrace else "❌",
            "Allowed Mentions": "\n".join(
                (
                    "",
                    f"- Everyone: {'✅' if log.allowed_mentions.everyone else '❌'}",
                    f"- Users: {'✅' if log.allowed_mentions.users else '❌'}",
                    f"- Roles: {'✅' if log.allowed_mentions.roles else '❌'}",
                    f"- Replied User: {'✅' if log.allowed_mentions.replied_user else '❌'}",
                )
            ),
        }

        # Create the default log details view
        view = ui.LayoutView()
        container = ui.Container(accent_color=0x00ACED)
        view.add_item(container)

        container.add_item(
            ui.TextDisplay(f"### 🧾 Details for default log channel <#{log.channel}>")
        )
        container.add_item(ui.Separator())
        for field_name, field_value in fields.items():
            container.add_item(ui.TextDisplay(f"**{field_name}**: {field_value}"))

        # Respond with the view
        await interaction.response.send_message(view=view)

    async def add_rule(self, interaction: Interaction):
        await interaction.response.send_modal(rule_ui.AddRuleModal(interaction, self))

    async def modify_rule(self, interaction: Interaction, name: str):
        rule = await self.store.require_rule(self.guild, name)
        await interaction.response.send_modal(
            rule_ui.ModifyRuleModal(interaction, self, rule)
        )

    async def upload_rule(self, interaction: Interaction, file: Attachment):
        # The uploaded file needs to be a Json file
        if not (file.content_type and MimeType.APPLICATION_JSON in file.content_type):
            raise UploadIsNotJsonFile

        # Try to validate the uploaded file
        try:
            file_data = await file.read()
            rule = AutomodRule.model_validate_json(file_data)
        except ValueError as ex:
            raise CouldNotValidateUploadedAutomodRule(ex)

        # Modify the rule if it already exists
        if await self.store.has_rule(self.guild, rule.name):
            await self.store.modify_rule(self.guild, rule, interaction.user.id)
            await interaction.response.send_message(f"Modified rule `{rule.name}`")
        else:
            await self.store.add_rule(self.guild, rule, interaction.user.id)
            await interaction.response.send_message(f"Added rule `{rule.name}`")

    async def remove_rule(self, interaction: Interaction, name: str):
        # Get the rule
        rule = await self.store.require_rule(self.guild, name)

        # Respond to this interaction with a confirmation dialog
        result: ConfirmationResult = await respond_with_confirmation(
            interaction,
            f"Are you sure you want to remove the rule `{rule.name}`?",
            timeout=10.0,
        )

        # Handle response to dialog
        match result:
            case ConfirmationResult.YES:
                try:
                    await self.store.remove_rule(self.guild, rule.name)
                    await interaction.followup.send(
                        content=f"Removed the rule `{rule.name}`"
                    )
                except Exception:
                    await interaction.delete_original_response()
                    raise
            case _:
                await interaction.followup.send(
                    f"Did not remove the rule `{rule.name}`"
                )

    async def show_rule_details(self, interaction: Interaction, name: str):
        # Get rule and metadata
        rule = await self.store.require_rule(self.guild, name)
        metadata = await self.store.require_rule_metadata(self.guild, name)

        # Turn the rule into a Json file
        rule_json = rule.model_dump_json(indent=4, exclude_defaults=True)
        rule_file = str_to_file(rule_json, f"{rule.name}.json")

        # Create fields
        description = f"`{rule.description}`" if rule.description else "**None!**"
        fields: dict[str, str] = {
            "Name": f"`{rule.name}`",
            "Description": description,
            "Enabled": "❌" if rule.disabled else "✅",
            "Hits": f"`{metadata.hits}`",
            "Added by": f"<@{metadata.added_by_id}>({format_dt(metadata.added_on, style='R')})",
            "Modified by": f"<@{metadata.modified_by_id}>({format_dt(metadata.modified_on, style='R')})",
        }

        # Create the rule details view
        view = ui.LayoutView()
        container = ui.Container(accent_color=0x00ACED)
        view.add_item(container)

        container.add_item(ui.TextDisplay(f"### 📜 Details for rule `{rule.name}`"))
        container.add_item(ui.Separator())
        container.add_item(ui.File(rule_file))
        container.add_item(ui.Separator())
        for field_name, field_value in fields.items():
            container.add_item(ui.TextDisplay(f"**{field_name}**: {field_value}"))

        # Respond with the view
        await interaction.response.send_message(
            view=view,
            file=rule_file,
            allowed_mentions=AllowedMentions.none(),
        )

    async def enable_rule(self, interaction: Interaction, name: str):
        rule = await self.store.enable_rule(self.guild, name)
        await interaction.response.send_message(f"Enabled rule `{rule.name}`")

    async def disable_rule(self, interaction: Interaction, name: str):
        rule = await self.store.disable_rule(self.guild, name)
        await interaction.response.send_message(f"Disabled rule `{rule.name}`")

    async def list_rules(self, interaction: Interaction):
        # Get info about rules
        formatted_rules: list[str] = []
        enabled_rules: int = 0
        disabled_rules: int = 0
        async for rule in self.store.yield_rules(self.guild):
            if not rule.disabled:
                formatted_rules.append(rule.name)
                enabled_rules += 1
            else:
                formatted_rules.append(f"{rule.name} (Disabled)")
                disabled_rules += 1

        # Create rule list view
        view = ui.LayoutView()
        container = ui.Container(accent_color=0x00ACED)
        view.add_item(container)

        container.add_item(ui.TextDisplay("### 📜 All rules"))
        container.add_item(ui.Separator())

        if formatted_rules:
            lines = "\n".join(("```", "\n".join(formatted_rules), "```"))
            container.add_item(ui.TextDisplay(lines))
        else:
            container.add_item(ui.TextDisplay("**None!**"))

        container.add_item(ui.Separator())
        container.add_item(
            ui.TextDisplay(f"-# Enabled: {enabled_rules} | Disabled: {disabled_rules}")
        )

        # Respond with the view
        await interaction.response.send_message(view=view)

    async def enable_all_rule(self, interaction: Interaction):
        rule_count = await self.store.rule_count(self.guild)
        await self.store.enable_all_rules(self.guild)
        await interaction.response.send_message(f"Enabled all `{rule_count}` rules")

    async def disable_all_rule(self, interaction: Interaction):
        rule_count = await self.store.rule_count(self.guild)
        await self.store.disable_all_rules(self.guild)
        await interaction.response.send_message(f"Disabled all `{rule_count}` rules")

    async def add_flagged_image_attachments_bucket(self, interaction: Interaction):
        pass

    async def add_message_history_bucket(self, interaction: Interaction):
        pass

    async def modify_bucket(self, interaction: Interaction, name: str):
        # Get the bucket
        bucket = await self.store.require_bucket(self.guild, name)

        # Send the right modal based on the bucket type
        match bucket:
            case buckets.FlaggedImageAttachments():
                pass
            case buckets.MessageHistory():
                pass
            case _:
                pass

    async def remove_bucket(self, interaction: Interaction, name: str):
        # Get the bucket
        bucket = await self.store.require_bucket(self.guild, name)

        # Respond to this interaction with a confirmation dialog
        result: ConfirmationResult = await respond_with_confirmation(
            interaction,
            f"Are you sure you want to remove the bucket `{bucket.name}`?",
            timeout=10.0,
        )

        # Handle response to dialog
        match result:
            case ConfirmationResult.YES:
                try:
                    await self.store.remove_bucket(self.guild, bucket.name)
                    await interaction.followup.send(
                        content=f"Removed the bucket `{bucket.name}`"
                    )
                except Exception:
                    await interaction.delete_original_response()
                    raise
            case _:
                await interaction.followup.send(
                    f"Did not remove the bucket `{bucket.name}`"
                )

    async def show_bucket_details(self, interaction: Interaction, name: str):
        # Get the bucket
        bucket = await self.store.require_bucket(self.guild, name)

        # Create fields
        description = f"`{bucket.description}`" if bucket.description else "**None!**"
        fields: dict[str, str] = {
            "Type": f"`{bucket.type}`",
            "Name": f"`{bucket.name}`",
            "Description": description,
            "Enabled": "❌" if bucket.disabled else "✅",
        }

        # Add any fields that are specific to the bucket type
        match bucket:
            case buckets.FlaggedImageAttachments():
                fields["Lifetime"] = f"`{bucket.lifetime}`"
                fields["Flagged"] = f"`{len(bucket.attachments)}`"
            case buckets.MessageHistory():
                fields["Lifetime"] = f"`{bucket.lifetime}`"
                fields["Interval"] = f"`{bucket.interval}`"
                fields["Messages"] = f"`{bucket.message_count}`"
                fields["Channels"] = f"`{bucket.channel_count}`"
            case _:
                pass

        # Create the bucket details view
        view = ui.LayoutView()
        container = ui.Container(accent_color=0x00ACED)
        view.add_item(container)

        container.add_item(ui.TextDisplay(f"### 🪣 Details for bucket `{bucket.name}`"))
        container.add_item(ui.Separator())
        for field_name, field_value in fields.items():
            container.add_item(ui.TextDisplay(f"**{field_name}**: {field_value}"))

        # Respond with the view
        await interaction.response.send_message(view=view)

    async def clear_bucket(self, interaction: Interaction, name: str):
        bucket = await self.store.clear_bucket(self.guild, name)
        await interaction.response.send_message(f"Cleared bucket `{bucket.name}`")

    async def enable_bucket(self, interaction: Interaction, name: str):
        bucket = await self.store.enable_bucket(self.guild, name)
        await interaction.response.send_message(f"Enabled bucket `{bucket.name}`")

    async def disable_bucket(self, interaction: Interaction, name: str):
        bucket = await self.store.disable_bucket(self.guild, name)
        await interaction.response.send_message(f"Disabled bucket `{bucket.name}`")

    async def list_buckets(self, interaction: Interaction):
        # Get info about buckets
        formatted_buckets: list[str] = []
        enabled_buckets: int = 0
        disabled_buckets: int = 0
        async for bucket in self.store.yield_buckets(self.guild):
            if not bucket.disabled:
                formatted_buckets.append(bucket.name)
                enabled_buckets += 1
            else:
                formatted_buckets.append(f"{bucket.name} (Disabled)")
                disabled_buckets += 1

        # Create bucket list view
        view = ui.LayoutView()
        container = ui.Container(accent_color=0x00ACED)
        view.add_item(container)

        container.add_item(ui.TextDisplay("### 🪣 All buckets"))
        container.add_item(ui.Separator())

        if formatted_buckets:
            lines = "\n".join(("```", "\n".join(formatted_buckets), "```"))
            container.add_item(ui.TextDisplay(lines))
        else:
            container.add_item(ui.TextDisplay("**None!**"))

        container.add_item(ui.Separator())
        container.add_item(
            ui.TextDisplay(
                f"-# Enabled: {enabled_buckets} | Disabled: {disabled_buckets}"
            )
        )

        # Respond with the view
        await interaction.response.send_message(view=view)

    async def clear_all_buckets(self, interaction: Interaction):
        bucket_count = await self.store.bucket_count(self.guild)
        await self.store.clear_all_buckets(self.guild)
        await interaction.response.send_message(f"Cleared all `{bucket_count}` buckets")

    async def enable_all_buckets(self, interaction: Interaction):
        bucket_count = await self.store.bucket_count(self.guild)
        await self.store.enable_all_buckets(self.guild)
        await interaction.response.send_message(f"Enabled all `{bucket_count}` buckets")

    async def disable_all_buckets(self, interaction: Interaction):
        bucket_count = await self.store.bucket_count(self.guild)
        await self.store.disable_all_buckets(self.guild)
        await interaction.response.send_message(
            f"Disabled all `{bucket_count}` buckets"
        )

    # @@ UTILITIES

    def get_schema_command(self) -> str:
        if cmd := get_app_command(self.bot, "automod schema"):
            return cmd.mention
        return "/automod schema"

    # @@ EVENTS

    async def _handle_rule_error(self, rule: AutomodRule, error: Exception):
        # Re-raise the error so that it can be printed to the console
        try:
            raise error
        except:
            self.log.exception(f"Automod rule '{rule.name}' caused an error")

        # Try to get the log channel
        log_channel = rule.log or await self.store.get_default_log(self.guild)
        if not log_channel:
            return

        # Attempt to print the error to the log channel
        try:
            await log_channel.send_error(
                self.bot, f"Automod rule `{rule.name}` caused an error", error
            )
        except:
            self.log.exception("Failed to send error message to log channel")

    async def _run_rule(self, rule: AutomodRule, event: AutomodEvent):
        try:
            context = AutomodContext(self.bot, self.log, self, rule, event)
            if await rule.run(context):
                await self.store.increment_rule_hits(self.guild, rule.name)
        except Exception as error:
            await self._handle_rule_error(rule, error)

    async def dispatch_event(self, event: AutomodEvent):
        async with asyncio.TaskGroup() as tg:
            async for rule in self.store.rules_for_event(self.guild, event):
                tg.create_task(self._run_rule(rule, event))

    # @@ DISCORD AUTOMOD
    async def on_discord_automod_action_block_message(
        self, execution: discord.AutoModAction
    ):
        await self.dispatch_event(events.DiscordAutomodBlockedMessage(execution))

    async def on_discord_automod_action_timeout(self, execution: discord.AutoModAction):
        await self.dispatch_event(events.DiscordAutomodTimedOut(execution))

    async def on_discord_automod_action_block_member_interactions(
        self, execution: discord.AutoModAction
    ):
        await self.dispatch_event(
            events.DiscordAutomodBlockedMemberInteractions(execution)
        )

    # @@ CHANNELS

    async def on_guild_channel_created(self, channel: GuildChannel):
        await self.dispatch_event(events.GuildChannelCreated(channel))

    async def on_guild_channel_deleted(self, channel: GuildChannel):
        await self.dispatch_event(events.GuildChannelDeleted(channel))

    async def on_guild_channel_updated(self, before: GuildChannel, after: GuildChannel):
        await self.dispatch_event(events.GuildChannelUpdated(before, after))

    async def on_guild_channel_pins_updated(
        self, channel: MessageableGuildChannel | Thread, last_pin: Optional[datetime]
    ):
        await self.dispatch_event(events.GuildChannelPinsUpdated(channel, last_pin))

    # @@ MEMBERS

    async def on_member_joined(self, member: Member):
        await self.dispatch_event(events.MemberJoined(member))

    async def on_member_left(self, member: Member):
        await self.dispatch_event(events.MemberLeft(member))

    async def on_member_typing(
        self, channel: MessageableGuildChannel | Thread, member: Member, when: datetime
    ):
        await self.dispatch_event(events.MemberTyping(channel, member, when))

    async def on_member_updated(self, before: Member, after: Member):
        await self.dispatch_event(events.MemberUpdated(before, after))

    # @@ MESSAGES

    async def on_message_sent(self, message: Message):
        await self.dispatch_event(events.MessageSent(message))

    async def on_message_edited(self, before: Message, after: Message):
        await self.dispatch_event(events.MessageEdited(before, after))

    async def on_message_deleted(self, message: Message):
        await self.dispatch_event(events.MessageDeleted(message))

    # @@ REACTIONS

    async def on_reaction_added(self, reaction: Reaction, member: Member):
        await self.dispatch_event(events.ReactionAdded(reaction, member))

    async def on_reaction_removed(self, reaction: Reaction, member: Member):
        await self.dispatch_event(events.ReactionRemoved(reaction, member))

    # @@ THREADS

    async def on_thread_created(self, thread: Thread):
        await self.dispatch_event(events.ThreadCreated(thread))

    async def on_thread_joined(self, thread: Thread):
        await self.dispatch_event(events.ThreadJoined(thread))

    async def on_thread_updated(self, before: Thread, after: Thread):
        await self.dispatch_event(events.ThreadUpdated(before, after))

    async def on_thread_removed(self, thread: Thread):
        await self.dispatch_event(events.ThreadRemoved(thread))

    async def on_thread_deleted(self, thread: Thread):
        await self.dispatch_event(events.ThreadDeleted(thread))

    async def on_thread_member_joined(self, member: ThreadMember):
        await self.dispatch_event(events.ThreadMemberJoined(member))

    async def on_thread_member_left(self, member: ThreadMember):
        await self.dispatch_event(events.ThreadMemberLeft(member))

    # @@ USERS

    async def on_user_updated(self, before: User, after: User):
        await self.dispatch_event(events.UserUpdated(before, after))

    async def on_user_banned(self, user: User):
        await self.dispatch_event(events.UserBanned(user))

    async def on_user_unbanned(self, user: User):
        await self.dispatch_event(events.UserUnbanned(user))
