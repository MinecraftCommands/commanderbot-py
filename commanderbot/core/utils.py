from typing import Optional, Type, TypeIs

from discord import Interaction
from discord.abc import Snowflake
from discord.app_commands import AppCommand
from discord.ext.commands import Bot, Cog

from commanderbot.core.commander_bot import CommanderBot
from commanderbot.lib import AppCommandID, GuildID


def is_commander_bot(obj: object) -> TypeIs[CommanderBot]:
    return isinstance(obj, CommanderBot)


def get_commander_bot(obj: object) -> Optional[CommanderBot]:
    if is_commander_bot(obj):
        return obj


def require_commander_bot(obj: object) -> CommanderBot:
    if is_commander_bot(obj):
        return obj
    raise TypeError("'obj' is not an instance of 'CommanderBot'")


async def add_configured_cog(bot: Bot, ext_name: str, cog_class: Type[Cog]):
    cog = None
    if is_commander_bot(bot):
        if options := bot.get_extension_options(ext_name):
            cog = cog_class(bot, **options)
    if not cog:
        cog = cog_class(bot)
    await bot.add_cog(cog)


def get_app_command(
    bot: Bot,
    command: str | Interaction | AppCommandID,
    *,
    guild: Optional[Snowflake | GuildID] = None,
) -> Optional[AppCommand]:
    # Return early if bot is not an instance of `CommanderBot`
    if not is_commander_bot(bot):
        return

    # Return early if we were passed an empty string
    if isinstance(command, str) and not command:
        return

    # If we were passed an interaction, check if it's for a command
    # and try extracting the qualified command name
    if isinstance(command, Interaction):
        if not command.command:
            return
        command = command.command.qualified_name

    # Try getting the app command
    return bot.command_tree.get_app_command(command, guild=guild)
