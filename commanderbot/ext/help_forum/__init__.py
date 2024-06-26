from discord.ext.commands import Bot

from commanderbot.core.utils import add_configured_cog
from commanderbot.ext.help_forum.help_forum_cog import HelpForumCog


async def setup(bot: Bot):
    await add_configured_cog(bot, __name__, HelpForumCog)
