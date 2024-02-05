from discord.ext.commands import Bot

from commanderbot.core.utils import add_configured_cog
from commanderbot.ext.feeds.feeds_cog import FeedsCog


async def setup(bot: Bot):
    await add_configured_cog(bot, __name__, FeedsCog)
