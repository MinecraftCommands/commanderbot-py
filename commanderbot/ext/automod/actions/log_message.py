from typing import Literal, Optional, override

from discord import File, Thread, ui
from pydantic import Field

from commanderbot.ext.automod.action import AutomodAction
from commanderbot.ext.automod.automod_context import AutomodContext
from commanderbot.ext.automod.types import ContextFields
from commanderbot.lib.allowed_mentions import AllowedMentions
from commanderbot.lib.color import Color
from commanderbot.lib.constants import MAX_MESSAGE_LENGTH
from commanderbot.lib.predicates import is_messagable_guild_channel, is_thread
from commanderbot.lib.types import ChannelID, MessageableGuildChannel
from commanderbot.lib.utils import message_to_file

__all__ = ("LogMessage",)


class LogMessage(AutomodAction):
    """
    Send a log message.
    """

    type: Literal["log_message"]

    content: str
    """The content of the message to send."""

    channel: Optional[ChannelID] = None
    """
    The channel to send the message in. If not set, the action will try to resolve
    other log channels that may be in context. The order for that is: the rule's log, the default log,
    and lastly the channel in context.
    """

    emoji: Optional[str] = None
    """The emoji used to represent the type of message."""

    color: Optional[Color] = None
    """The color used to represent the type of message."""

    attach_message: bool = False
    """Whether to attach the message-in-context to the log message or not."""

    attach_media: bool = False
    """Whether to attach image/video attachments to the log message or not."""

    fields: Optional[dict[ContextFields, str]] = None
    """
    A custom set of fields to display as part of the message. The key should
    correspond to a context field, and the value is the title to use for it.
    """

    allowed_mentions: AllowedMentions = Field(default_factory=AllowedMentions.none)
    """
    The types of mentions allowed in the message. Unless otherwise specified, all
    mentions will be suppressed.
    """

    async def _resolve_channel(
        self, context: AutomodContext
    ) -> Optional[MessageableGuildChannel | Thread]:
        # Try to resolve the action's log channel
        if self.channel is not None:
            channel = context.bot.get_channel(self.channel)
            if is_messagable_guild_channel(channel) or is_thread(channel):
                return channel

        # Try to resolve the rule's log channel
        if (rule_log := context.rule.log) and (channel_id := rule_log.channel):
            channel = context.bot.get_channel(channel_id)
            if is_messagable_guild_channel(channel) or is_thread(channel):
                return channel

        # Try to resolve the default log channel
        default_log = await context.state.store.get_default_log(context.state.guild)
        if default_log and (channel_id := default_log.channel):
            channel = context.bot.get_channel(channel_id)
            if is_messagable_guild_channel(channel) or is_thread(channel):
                return channel

        # Try to resolve the channel in context
        if context.event.channel and (channel_id := context.event.channel.id):
            channel = context.bot.get_channel(channel_id)
            if is_messagable_guild_channel(channel) or is_thread(channel):
                return channel

    def _build_log_view(
        self, context: AutomodContext
    ) -> tuple[ui.LayoutView, list[File]]:
        log_view = ui.LayoutView()
        log_container = ui.Container(accent_color=self.color)
        log_view.add_item(log_container)

        # Create the title
        title: Optional[str] = None
        if self.emoji:
            title = f"### {self.emoji} {context.rule.name}"
        else:
            title = f"### {context.rule.name}"
        log_container.add_item(ui.TextDisplay(title))

        # Add content
        content = context.format_content(self.content)
        log_container.add_item(ui.Separator())
        log_container.add_item(ui.TextDisplay(content))

        files: list[File] = []
        if message := context.event.message:
            # Add message if it needs to be attached
            if self.attach_message and message.content:
                log_container.add_item(ui.Separator())
                if len(message.content) > MAX_MESSAGE_LENGTH:
                    file = message_to_file(message)
                    files.append(file)
                    log_container.add_item(ui.File(file))
                else:
                    formatted_content = f"```\n{message.content}\n```"
                    log_container.add_item(ui.TextDisplay(formatted_content))

                    file = message_to_file(message)
                    files.append(file)
                    log_container.add_item(ui.File(file))

            # Attach media if it needs to be attached
            if self.attach_media and (attachments := context.event.attachments):
                gallery = ui.MediaGallery()
                has_media: bool = False
                for attachment in attachments:
                    content_type = attachment.content_type
                    if content_type and content_type.startswith(("image", "video")):
                        has_media = True
                        gallery.add_item(media=attachment.url)
                if has_media:
                    log_container.add_item(ui.Separator())
                    log_container.add_item(gallery)

        # Add fields if any were specified
        if self.fields:
            field_lines = []
            context_fields = context.get_fields()
            for field_name, field_title in self.fields.items():
                if field_value := context_fields.get(field_name):
                    field_lines.append(f"- **{field_title}**: `{field_value}`")

            if field_lines:
                log_container.add_item(ui.Separator())
                log_container.add_item(ui.TextDisplay("\n".join(field_lines)))

        return (log_view, files)

    @override
    async def apply(self, context: AutomodContext):
        channel = await self._resolve_channel(context)
        if not channel:
            return

        view, files = self._build_log_view(context)
        await channel.send(
            view=view, files=files, allowed_mentions=self.allowed_mentions
        )
