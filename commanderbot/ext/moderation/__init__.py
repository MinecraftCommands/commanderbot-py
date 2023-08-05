from discord.ext.commands import Bot

from commanderbot.ext.moderation.moderation_cog import ModerationCog


async def setup(bot: Bot):
    await bot.add_cog(ModerationCog(bot))
