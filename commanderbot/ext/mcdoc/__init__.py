from discord.ext.commands import Bot

from commanderbot.core.utils import is_commander_bot
from commanderbot.ext.mcdoc.mcdoc_cog import McdocCog


async def setup(bot: Bot):
    await bot.add_cog(McdocCog(bot))
