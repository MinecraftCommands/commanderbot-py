from typing import Optional

from discord import Attachment, Emoji
from discord.ext.commands import Bot

from commanderbot.core.exceptions import ApplicationEmojiDoesNotExist
from commanderbot.lib import EmojiID


class ApplicationEmojiManager:
    def __init__(self, bot: Bot):
        self._bot: Bot = bot
        self._cache: dict[str, Emoji] = {}

    def _get_from_cache(self, emoji: str | EmojiID) -> Optional[Emoji]:
        # Try to find the emoji by its name
        if isinstance(emoji, str):
            if e := self._cache.get(emoji):
                return e

        # Try to find the emoji by its ID
        if isinstance(emoji, EmojiID):
            for e in self._cache.values():
                if e.id == emoji:
                    return e

    async def update_cache(self):
        """
        Update the application emoji cache.

        Raises
        ------
        MissingApplicationID
            The application ID could not be found.
        HTTPException
            Retrieving the emojis failed.
        """

        emojis = await self._bot.fetch_application_emojis()
        self._cache = {e.name: e for e in emojis}

    async def fetch(self, emoji: str | EmojiID, /, *, use_cache: bool = True) -> Emoji:
        """
        Fetch an application emoji from Discord, or from the cache if it already exists.

        Parameters
        ----------
        emoji: :class:`str | EmojiID`
            The emoji to fetch.
        use_cache: :class:`bool`
            Should the cache be used.

        Raises
        ------
        ApplicationEmojiDoesNotExist
            The application emoji does not exist.
        MissingApplicationID
            The application ID could not be found.
        HTTPException
            Retrieving the emojis failed.
        """

        if not use_cache or not self._cache:
            await self.update_cache()

        if found_emoji := self._get_from_cache(emoji):
            return found_emoji
        raise ApplicationEmojiDoesNotExist(emoji)

    async def fetch_all(self, *, use_cache: bool = True) -> list[Emoji]:
        """
        Fetch all application emojis from Discord, or from the cache.

        Parameters
        ----------
        use_cache: :class:`bool`
            Should the cache be used.

        Raises
        ------
        MissingApplicationID
            The application ID could not be found.
        HTTPException
            Retrieving the emojis failed.
        """

        if not use_cache or not self._cache:
            await self.update_cache()
        return list(self._cache.values())

    def get(self, emoji: str | EmojiID) -> Optional[Emoji]:
        """
        Get an application emoji from the cache. It may or may not exist.

        Parameters
        ----------
        emoji: :class:`str | EmojiID`
            The emoji to get.
        """

        return self._get_from_cache(emoji)

    def get_all(self) -> list[Emoji]:
        """
        Get all application emojis from the cache. They may or may not exist.
        """

        return list(self._cache.values())

    async def create(self, name: str, image: bytes | Attachment) -> Emoji:
        """
        Create an application emoji.

        Parameters
        ----------
        name: :class:`str`
            The emoji name.
        image: :class:`bytes | Attachment`
            The image for this emoji.

        Raises
        ------
        MissingApplicationID
            The application ID could not be found.
        HTTPException
            Creating the emoji failed or retrieving the emojis failed.
        """

        # Get the emoji image
        data: Optional[bytes] = None
        if isinstance(image, Attachment):
            data = await image.read()
        else:
            data = image

        # Create the emoji
        emoji: Emoji = await self._bot.create_application_emoji(name=name, image=data)
        await self.update_cache()
        return emoji

    async def edit(self, emoji: str | EmojiID, new_name: str) -> Emoji:
        """
        Edit an application emoji.

        Parameters
        ----------
        emoji: :class:`str | EmojiID`
            The emoji to edit.
        new_name: :class:`str`
            The new name for this emoji.

        Raises
        ------
        ApplicationEmojiDoesNotExist
            The application emoji does not exist.
        MissingApplicationID
            The application ID could not be found.
        HTTPException
            Editing the emoji failed or retrieving the emojis failed.
        """

        if not self._cache:
            await self.update_cache()

        # Edit the emoji
        if found_emoji := self._get_from_cache(emoji):
            edited_emoji: Emoji = await found_emoji.edit(name=new_name)
            await self.update_cache()
            return edited_emoji
        else:
            raise ApplicationEmojiDoesNotExist(emoji)

    async def delete(self, emoji: str | EmojiID):
        """
        Delete an application emoji.

        Parameters
        ----------
        emoji: :class:`str | EmojiID`
            The emoji to delete.

        Raises
        ------
        ApplicationEmojiDoesNotExist
            The application emoji does not exist.
        MissingApplicationID
            The application ID could not be found.
        HTTPException
            Deleting the emoji failed or retrieving the emojis failed.
        """

        if not self._cache:
            await self.update_cache()

        # Delete the emoji
        if found_emoji := self._get_from_cache(emoji):
            await found_emoji.delete()
            await self.update_cache()
        else:
            raise ApplicationEmojiDoesNotExist(emoji)
