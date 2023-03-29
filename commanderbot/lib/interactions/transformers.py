import re
from typing import List

from discord import Interaction, Message
from discord.app_commands import AppCommandError, Choice, Transformer
from discord.ext.commands import BadArgument, CommandError, Context, MessageConverter
from emoji import is_emoji

from commanderbot.lib.color import Color
from commanderbot.lib.constants import MAX_AUTOCOMPLETE_CHOICES
from commanderbot.lib.responsive_exception import ResponsiveException

__all__ = (
    "InvalidEmoji",
    "InvalidMessageLink",
    "UnableToFindMessage",
    "InvalidColor",
    "EmojiTransformer",
    "MessageTransformer",
    "ColorTransformer",
)


CUSTOM_EMOJI_PATTERN = re.compile(r"\<a?\:\w+\:\d+\>")
MESSAGE_LINK_PATTERN = re.compile(
    r"https:\/\/discord(?:app)?.com\/channels\/(\d+|@me)\/(\d+)\/(\d+)"
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
        elif CUSTOM_EMOJI_PATTERN.match(value):
            return value
        raise InvalidEmoji(value)


class MessageTransformer(Transformer):
    """
    Transforms a valid Discord message link into a `discord.Message`
    """

    async def transform(self, interaction: Interaction, value: str) -> Message:
        # Return early if the string we're trying to transform isn't a valid Discord message link
        if not MESSAGE_LINK_PATTERN.match(value):
            raise InvalidMessageLink(value)

        # Try to transform `value` into a `discord.Message`
        try:
            ctx = await Context.from_interaction(interaction)  # type: ignore
            return await MessageConverter().convert(ctx, value)  # type: ignore
        except (CommandError, BadArgument):
            raise UnableToFindMessage(value)


class ColorTransformer(Transformer):
    async def transform(self, interaction: Interaction, value: str) -> Color:
        try:
            return Color.from_str(value)
        except ValueError:
            raise InvalidColor(value)

    async def autocomplete(
        self, interaction: Interaction, value: str
    ) -> List[Choice[str]]:
        colors: list[Choice] = []
        for (i, (name, color)) in enumerate(Color.presets(color_filter=value).items()):
            if i == MAX_AUTOCOMPLETE_CHOICES:
                break
            colors.append(Choice(name=name, value=color.to_hex()))

        return colors
