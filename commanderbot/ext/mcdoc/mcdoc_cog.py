from logging import Logger, getLogger
from typing import Optional
import aiohttp

from discord import Embed, Emoji, Interaction
from discord.app_commands import (
    allowed_contexts,
    allowed_installs,
    command,
    describe,
)
from discord.ext import tasks
from discord.ext.commands import Bot, Cog

from commanderbot.core.commander_bot import CommanderBot
from commanderbot.ext.mcdoc.mcdoc_symbols import McdocSymbols
from commanderbot.ext.mcdoc.mcdoc_types import McdocContext
from commanderbot.ext.mcdoc.mcdoc_exceptions import InvalidVersionError, RequestSymbolsError, RequestVersionError, EmojiNotFoundError
from commanderbot.ext.mcdoc.mcdoc_options import McdocOptions
from commanderbot.lib import constants, AllowedMentions


class McdocCog(Cog, name="commanderbot.ext.mcdoc"):
    def __init__(self, bot: CommanderBot, **options):
        self.bot: CommanderBot = bot
        self.log: Logger = getLogger(self.qualified_name)
        self.options = McdocOptions.from_data(options)

        self._latest_version: Optional[str] = None
        self._symbols: Optional[McdocSymbols] = None
        self._etag: Optional[str] = None

    async def cog_load(self):
        self._fetch_latest_version.start()

    async def cog_unload(self):
        self._fetch_latest_version.stop()

    async def _fetch_symbols(self) -> McdocSymbols:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.options.symbols_url,
                    headers={
                        "User-Agent": constants.USER_AGENT,
                        "If-None-Match": self._etag or "",
                    },
                ) as response:
                    # Use cached symbols if they are still valid
                    if response.status == 304 and self._symbols:
                        return self._symbols

                    if response.status != 200:
                        raise RequestSymbolsError()

                    # Store symbol data and ETag header
                    data: dict = await response.json()
                    self._symbols = McdocSymbols(data)
                    self.etag = response.headers.get("ETag")

                    return self._symbols

        except aiohttp.ClientError:
            raise RequestSymbolsError()

    @tasks.loop(hours=1)
    async def _fetch_latest_version(self) -> str:
        try:
            # Try to update the version
            async with aiohttp.ClientSession(raise_for_status=True) as session:
                async with session.get(self.options.manifest_url, headers={
                    "User-Agent": constants.USER_AGENT,
                }) as response:
                    data: dict = await response.json()
                    release: str = data["latest"]["release"]
                    self._latest_version = release
                    return self._latest_version

        except aiohttp.ClientError:
            raise RequestVersionError()

    async def _get_latest_version(self, override: Optional[str]) -> str:
        if override:
            return override
        if self._latest_version:
            return self._latest_version
        return await self._fetch_latest_version()

    def _get_emoji(self, type: str) -> Emoji:
        name = self.options.emoji_prefix + type
        emoji = self.bot.application_emojis.get(name)
        if emoji is None:
            raise EmojiNotFoundError(name)
        return emoji

    @command(name="mcdoc", description="Query vanilla mcdoc types")
    @describe(
        query="The mcdoc identifier",
        version="The Minecraft game version (defaults to the latest release)",
    )
    @allowed_installs(guilds=True, users=True)
    @allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def cmd_mcdoc(self, interaction: Interaction, query: str, version: Optional[str]):
        # Respond to the interaction with a defer since the web request may take a while
        await interaction.response.defer()

        # Fetch the vanilla-mcdoc symbols and search for a symbol
        symbols = await self._fetch_symbols()
        symbol = symbols.search(query)

        # Use the version override or get the cached latest version
        version = await self._get_latest_version(version)

        # Validate that the version number can be used to compare
        if not version.startswith("1."):
            raise InvalidVersionError(version)
        try:
            float(version[2:])
        except:
            raise InvalidVersionError(version)

        # Create a context object used for rendering
        ctx = McdocContext(version, symbols, self._get_emoji)

        embed: Embed = Embed(
            title=symbol.title(ctx),
            description=symbol.body(ctx),
            color=0x2783E3, # Spyglass blue
        )
        embed.set_footer(text=f"vanilla-mcdoc · {version}", icon_url=self.options.icon_url)

        await interaction.followup.send(embed=embed, allowed_mentions=AllowedMentions.none())
