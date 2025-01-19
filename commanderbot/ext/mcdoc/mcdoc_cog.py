from logging import Logger, getLogger
from typing import Optional
import aiohttp
import re

from discord import Embed, Interaction
from discord.app_commands import (
    allowed_contexts,
    allowed_installs,
    command,
    describe,
)
from discord.ext.commands import Bot, Cog

from commanderbot.ext.mcdoc.mcdoc_symbols import McdocSymbols
from commanderbot.ext.mcdoc.mcdoc_types import McdocContext
from commanderbot.ext.mcdoc.mcdoc_exceptions import RequestError
from commanderbot.lib import constants, AllowedMentions

MCDOC_SYMBOLS_URL = "https://api.spyglassmc.com/vanilla-mcdoc/symbols"
SPYGLASS_ICON_URL = "https://avatars.githubusercontent.com/u/74945225?s=64"


class McdocCog(Cog, name="commanderbot.ext.mcdoc"):
    def __init__(self, bot: Bot):
        self.bot: Bot = bot
        self.log: Logger = getLogger(self.qualified_name)
        self.symbols: Optional[McdocSymbols] = None

        self._etag: Optional[str] = None

    async def _fetch_symbols(self) -> McdocSymbols:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    MCDOC_SYMBOLS_URL,
                    headers={
                        "User-Agent": constants.USER_AGENT,
                        "If-None-Match": self._etag or "",
                    },
                ) as response:
                    # Use cached symbols if they are still valid
                    if response.status == 304 and self.symbols:
                        return self.symbols

                    if response.status != 200:
                        raise RequestError()

                    # Store symbol data and ETag header
                    data: dict = await response.json()
                    self.symbols = McdocSymbols(data)
                    etag = response.headers.get("ETag")
                    if etag:
                        self._etag = etag.removeprefix('W/"').removesuffix('"')

                    return self.symbols

        except aiohttp.ClientError:
            raise RequestError()

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

        symbols = await self._fetch_symbols()
        symbol = symbols.search(query)

        # TODO: un-hardcode the latest release version
        ctx = McdocContext(version or "1.21.4", symbols)

        embed: Embed = Embed(
            title=symbol.title(ctx),
            description=symbol.typeDef.render(ctx),
            color=0x2783E3,
        )
        embed.set_footer(text=f"vanilla-mcdoc · {ctx.version}", icon_url=SPYGLASS_ICON_URL)

        await interaction.followup.send(embed=embed, allowed_mentions=AllowedMentions.none())
