from discord import Embed, Interaction
from discord.app_commands import allowed_installs, command
from discord.ext.commands import Bot, Cog

from commanderbot.ext.status.status_details import StatusDetails


class StatusCog(Cog, name="commanderbot.ext.status"):
    def __init__(self, bot: Bot):
        self.bot: Bot = bot

    @command(name="status", description="Shows the status of the bot")
    @allowed_installs(guilds=True)
    async def cmd_status(self, interaction: Interaction):
        status_details = StatusDetails(self.bot)

        status_embed: Embed = Embed(color=0x00ACED)
        for k, v in status_details.fields.items():
            status_embed.add_field(name=k, value=v)

        await interaction.response.send_message(embed=status_embed)
