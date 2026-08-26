from typing import Optional

from discord import File, Thread, ui
from discord.ext.commands import Bot
from pydantic import BaseModel, ConfigDict, Field

from commanderbot.lib.allowed_mentions import AllowedMentions
from commanderbot.lib.color import Color
from commanderbot.lib.constants import MAX_MESSAGE_LENGTH
from commanderbot.lib.exceptions import ResponsiveException
from commanderbot.lib.predicates import is_messagable_guild_channel, is_thread
from commanderbot.lib.types import ChannelID, MessageableGuildChannel
from commanderbot.lib.utils import sanitize_stacktrace, str_to_file

__all__ = ("LogChannel",)


class LogChannel(BaseModel):
    """
    Configures a channel to be used for logging.
    """

    model_config = ConfigDict(use_attribute_docstrings=True)

    channel: ChannelID
    """The channel to send log messages in."""

    emoji: Optional[str] = None
    """The emoji used to represent the type of log message."""

    color: Optional[Color] = None
    """The color used to represent the type of log message."""

    stacktrace: Optional[bool] = None
    """Whether to print exception stacktraces."""

    allowed_mentions: AllowedMentions = Field(default_factory=AllowedMentions.none)
    """
    The types of mentions allowed in the log message. Unless otherwise specified, all
    mentions will be suppressed.
    """

    async def _require_channel(self, bot: Bot) -> MessageableGuildChannel | Thread:
        if channel := bot.get_channel(self.channel):
            if is_messagable_guild_channel(channel) or is_thread(channel):
                return channel
            raise ResponsiveException(
                f"Resolved a log channel that isn't messageable: '{self.channel}'"
            )
        raise ResponsiveException(
            f"Failed to resolve a log channel with ID '{self.channel}'"
        )

    def _format_error(self, exception: Exception) -> str:
        msg: Optional[str] = None
        if self.stacktrace:
            msg = sanitize_stacktrace(exception)
        else:
            msg = str(exception)
        return f"```python\n{msg}\n```"

    async def send(
        self,
        bot: Bot,
        title: str,
        content: str,
        *,
        file_name: str = "log.txt",
        allowed_mentions: Optional[AllowedMentions] = None,
    ):
        """
        Sends a message to the configured log channel.
        If the message is too big, it will be sent as a file instead.
        """
        channel = await self._require_channel(bot)
        allowed_mentions = allowed_mentions or self.allowed_mentions

        # Create log message view
        log_view = ui.LayoutView()
        log_container = ui.Container(accent_color=self.color)
        log_view.add_item(log_container)

        # Add title
        formatted_title: Optional[str] = None
        if self.emoji:
            formatted_title = f"### {self.emoji} {title}"
        else:
            formatted_title = f"### {title}"
        log_container.add_item(ui.TextDisplay(formatted_title))

        # Add content
        files: list[File] = []
        if len(content) > MAX_MESSAGE_LENGTH:
            file = str_to_file(content, file_name)
            files.append(file)
            log_container.add_item(ui.File(file))
        else:
            log_container.add_item(ui.TextDisplay(content))

        # Send the log message
        await channel.send(
            view=log_view, files=files, allowed_mentions=allowed_mentions
        )

    async def send_error(
        self,
        bot: Bot,
        title: str,
        error: Exception,
        *,
        file_name: str = "error.txt",
        allowed_mentions: Optional[AllowedMentions] = None,
    ):
        """
        Sends an error to the configured log channel.
        If the error message is too big, it will be sent as a file instead.
        """
        await self.send(
            bot,
            title,
            self._format_error(error),
            file_name=file_name,
            allowed_mentions=allowed_mentions,
        )

    async def send_view(
        self,
        bot: Bot,
        view: ui.View | ui.LayoutView,
        *,
        files: Optional[list[File]] = None,
        allowed_mentions: Optional[AllowedMentions] = None,
    ):
        """Send a view to the configured log channel."""
        channel = await self._require_channel(bot)
        files = files or []
        allowed_mentions = allowed_mentions or self.allowed_mentions

        await channel.send(view=view, files=files, allowed_mentions=allowed_mentions)
