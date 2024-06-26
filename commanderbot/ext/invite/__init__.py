from discord.ext.commands import Bot

from commanderbot.core.utils import add_configured_cog
from commanderbot.ext.invite.invite_cog import InviteCog


async def setup(bot: Bot):
    await add_configured_cog(bot, __name__, InviteCog)
