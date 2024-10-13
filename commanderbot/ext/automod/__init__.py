from discord.ext.commands import Bot

from commanderbot.core.utils import is_commander_bot
from commanderbot.ext.automod.automod_cog import AutomodCog


async def setup(bot: Bot):
    assert is_commander_bot(bot)
    await bot.add_configured_cog(__name__, AutomodCog)
