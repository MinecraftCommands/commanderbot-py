from typing import Optional, Iterable

from discord import Attachment, Emoji
from discord.ext.commands import Bot

from commanderbot.core.exceptions import ApplicationEmojiDoesNotExist
from commanderbot.lib import EmojiID


class ApplicationEmojiManager:
    def __init__(self, bot: Bot):
        self._bot: Bot = bot
        self._cache: dict[str, Emoji] = {}

    async def _update_cache(self):
        emojis = await self._bot.fetch_application_emojis()
        self._cache = {e.name: e for e in emojis}

    def _find_in_cache(self, emoji: str | EmojiID) -> Emoji:
        # Try to find the emoji by its name
        if isinstance(emoji, str):
            if e := self._cache.get(emoji):
                return e

        # Try to find the emoji by its ID
        if isinstance(emoji, EmojiID):
            for e in self._cache.values():
                if e.id == emoji:
                    return e

        raise ApplicationEmojiDoesNotExist(emoji)

    async def fetch(self, emoji: str | EmojiID) -> Emoji:
        """
        Fetch an application emoji from Discord, or from the cache if it already exists.

        Parameters
        ----------
        emoji: :class:`str | EmojiID`
            The emoji to fetch.

        Raises
        ------
        ApplicationEmojiDoesNotExist
            The application emoji does not exist.
        """

        if not self._cache:
            await self._update_cache()
        return self._find_in_cache(emoji)

    async def fetch_all(self) -> Iterable[Emoji]:
        """
        Fetch all application emojis from Discord, or from the cache.
        """

        if not self._cache:
            await self._update_cache()
        return self._cache.values()

    async def create(self, name: str, image: bytes | Attachment) -> Emoji:
        """
        Create an application emoji.

        Parameters
        ----------
        name: :class:`str`
            The emoji name.
        image: :class:`bytes | Attachment`
            The image for this emoji.
        """

        # Get the emoji image
        data: Optional[bytes] = None
        if isinstance(image, Attachment):
            data = await image.read()
        else:
            data = image

        # Create the emoji
        emoji = await self._bot.create_application_emoji(name=name, image=data)
        await self._update_cache()
        return emoji

    async def delete(self, emoji: str | EmojiID):
        """
        Delete an application emoji.

        Parameters
        ----------
        name: :class:`str`
            The emoji name.

        Raises
        ------
        ApplicationEmojiDoesNotExist
            The application emoji does not exist.
        """

        if not self._cache:
            await self._update_cache()

        # Delete the emoji
        found_emoji = self._find_in_cache(emoji)
        await found_emoji.delete()
        await self._update_cache()
