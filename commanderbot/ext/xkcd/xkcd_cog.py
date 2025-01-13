from discord import Embed, Interaction
from discord.app_commands import (
    Choice,
    Range,
    allowed_contexts,
    allowed_installs,
    autocomplete,
    command,
    describe,
)
from discord.ext.commands import Bot, GroupCog

from commanderbot.ext.xkcd.xkcd_client import PartialXKCDComic, XKCDClient, XKCDComic
from commanderbot.ext.xkcd.xkcd_options import XKCDOptions
from commanderbot.lib import constants, utils


@allowed_installs(guilds=True, users=True)
@allowed_contexts(guilds=True, dms=True, private_channels=True)
class XKCDCog(
    GroupCog,
    name="commanderbot.ext.xkcd",
    group_name="xkcd",
    description="View xkcd comics",
):
    def __init__(self, bot: Bot, **options):
        self.bot: Bot = bot
        self.options = XKCDOptions.from_data(options)
        self.xkcd_client = XKCDClient.from_options(self.options)

    # @@ UTILITIES

    def _create_comic_embed(self, comic: XKCDComic) -> Embed:
        embed = Embed(
            title=f"#{comic.num} {comic.title}",
            description=(
                f"-# This comic is interactive; check it out on the website!"
                if comic.interactive
                else ""
            ),
            url=comic.url,
            color=0x00ACED,
        )
        embed.set_image(url=comic.image_url)
        embed.set_footer(
            text=f"{comic.description}\n\nPublished: {comic.publication_date.strftime("%Y/%m/%d")}"
        )
        return embed

    # @@ AUTOCOMPLETE

    async def comic_autocomplete(
        self, interaction: Interaction, value: str
    ) -> list[Choice[int]]:
        """
        An autocomplete callback that will return any comics that match `value`
        """

        # Get all comics filtered by `value`
        comics: list[PartialXKCDComic] = await utils.async_expand(
            self.xkcd_client.get_comics_matching(
                comic_filter=value, sort=True, cap=constants.MAX_AUTOCOMPLETE_CHOICES
            )
        )

        # Create autocomplete choices and return them
        choices: list[Choice] = []
        for comic in comics:
            choices.append(
                Choice(name=f"📰 #{comic.num} {comic.title}", value=comic.num)
            )

        return choices

    # @@ COMMANDS

    # @@ xkcd get
    @command(name="get", description="Get an xkcd comic")
    @describe(query="The xkcd comic to get")
    @autocomplete(query=comic_autocomplete)
    async def cmd_xkcd_get(self, interaction: Interaction, query: Range[int, 1]):
        # Respond with a defer since requesting the comic may take a while
        await interaction.response.defer()

        # Try to get the comic
        try:
            comic: XKCDComic = await self.xkcd_client.get_comic(query)
        except Exception as ex:
            await interaction.delete_original_response()
            raise ex

        # Respond with the comic
        await interaction.followup.send(embed=self._create_comic_embed(comic))

    # @@ xkcd latest
    @command(name="latest", description="Get the latest xkcd comic")
    async def cmd_xkcd_latest(self, interaction: Interaction):
        # Respond with a defer since requesting the comic may take a while
        await interaction.response.defer()

        # Try to get the comic
        try:
            comic: XKCDComic = await self.xkcd_client.get_latest_comic()
        except Exception as ex:
            await interaction.delete_original_response()
            raise ex

        # Respond with the comic
        await interaction.followup.send(embed=self._create_comic_embed(comic))

    # @@ xkcd random
    @command(name="random", description="Get a random xkcd comic")
    async def cmd_xkcd_random(self, interaction: Interaction):
        # Respond with a defer since requesting the comic may take a while
        await interaction.response.defer()

        # Try to get the comic
        try:
            comic: XKCDComic = await self.xkcd_client.get_random_comic()
        except Exception as ex:
            await interaction.delete_original_response()
            raise ex

        # Respond with the comic
        await interaction.followup.send(embed=self._create_comic_embed(comic))
