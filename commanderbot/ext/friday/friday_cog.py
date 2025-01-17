from discord import Interaction
from discord.app_commands import (
    allowed_contexts,
    allowed_installs,
    command,
    default_permissions,
)
from discord.ext.commands import Bot, GroupCog

from commanderbot.lib import MessageableChannel, is_guild


@allowed_installs(guilds=True)
@allowed_contexts(guilds=True)
@default_permissions(administrator=True)
class FridayCog(
    GroupCog,
    name="commanderbot.ext.friday",
    group_name="friday",
    description="Today is friday in California",
):
    def __init__(self, bot: Bot):
        self.bot: Bot = bot

    @command(name="announcement", description="Send a message to a channel")
    async def cmd_friday_announcement(
        self, interaction: Interaction, channel: MessageableChannel, message: str
    ):
        pass
