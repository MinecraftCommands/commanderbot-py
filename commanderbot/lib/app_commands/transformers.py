from itertools import islice

from discord import Interaction, Message
from discord.app_commands import AppCommandError, Choice, Transformer
from discord.ext.commands import BadArgument, CommandError, Context, MessageConverter
from discord.interactions import Interaction
from emoji import is_emoji

from commanderbot.lib.color import Color
from commanderbot.lib.constants import MAX_AUTOCOMPLETE_CHOICES
from commanderbot.lib.exceptions import ResponsiveException
from commanderbot.lib.utils.utils import is_custom_emoji, is_message_link

__all__ = (
    "InvalidEmoji",
    "InvalidMessageLink",
    "UnableToFindMessage",
    "InvalidColor",
    "EmojiTransformer",
    "MessageTransformer",
    "ColorTransformer",
)


class TransformerException(ResponsiveException, AppCommandError):
    pass


class InvalidEmoji(TransformerException):
    def __init__(self, emoji: str):
        self.emoji = emoji
        super().__init__(f"😬 `{self.emoji}` is not a valid Discord or Unicode emoji")


class InvalidMessageLink(TransformerException):
    def __init__(self, message_link: str):
        self.message_link = message_link
        super().__init__(f"😬 `{message_link}` is not a valid Discord message link")


class UnableToFindMessage(TransformerException):
    def __init__(self, message_link: str):
        self.message_link = message_link
        super().__init__(f"😳 I can't find the message at {self.message_link}")


class InvalidColor(TransformerException):
    def __init__(self, color: str):
        self.color = color
        super().__init__(
            f"😬 `{self.color}` is not a valid color\n"
            "The supported color formats are "
            "`0x<hex>`, `#<hex>`, `0x#<hex>`, and `rgb(<number>, <number>, <number>)`"
        )


class EmojiTransformer(Transformer):
    """
    A transformer that validates that a string is a valid Unicode or Discord emoji
    """

    async def transform(self, interaction: Interaction, value: str) -> str:
        if is_emoji(value):
            return value
        elif is_custom_emoji(value):
            return value
        raise InvalidEmoji(value)


class MessageTransformer(Transformer):
    """
    Transforms a valid Discord message link into a `discord.Message`
    """

    async def transform(self, interaction: Interaction, value: str) -> Message:
        # Return early if the string we're trying to transform isn't a valid Discord message link
        if not is_message_link(value):
            raise InvalidMessageLink(value)

        # Try to transform `value` into a `discord.Message`
        try:
            ctx = await Context.from_interaction(interaction)  # type: ignore
            return await MessageConverter().convert(ctx, value)  # type: ignore
        except (CommandError, BadArgument):
            raise UnableToFindMessage(value)


class ColorTransformer(Transformer):
    """
    Transforms a string into a `commanderbot.lib.Color` (Subclass of `discord.Color`)

    Also provides autocomplete suggestions
    """

    async def transform(self, interaction: Interaction, value: str) -> Color:
        try:
            return Color.from_str(value)
        except ValueError:
            raise InvalidColor(value)

    async def autocomplete(
        self, interaction: Interaction, value: str
    ) -> list[Choice[str]]:
        colors: list[Choice] = []
        for name, color in islice(
            Color.presets(color_filter=value).items(), MAX_AUTOCOMPLETE_CHOICES
        ):
            colors.append(Choice(name=name, value=color.to_hex()))

        return colors
