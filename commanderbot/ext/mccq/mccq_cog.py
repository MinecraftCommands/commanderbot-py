from logging import Logger, getLogger
from typing import Optional

import aiohttp
from discord import Activity, ActivityType, Embed, Interaction, ui
from discord.app_commands import (
    Group,
    command,
    default_permissions,
    describe,
    guild_only,
)
from discord.ext import tasks
from discord.ext.commands import Bot, Cog

from commanderbot.ext.mccq.mccq_exceptions import (
    BedrockQueryManagerNotConfigured,
    JavaQueryManagerNotConfigured,
)
from commanderbot.ext.mccq.mccq_manager import MCCQManager
from commanderbot.ext.mccq.mccq_options import MCCQOptions
from commanderbot.lib import AllowedMentions
from commanderbot.lib.constants import MAX_MESSAGE_LENGTH, USER_AGENT
from commanderbot.lib.app_commands import checks
from commanderbot.lib.utils import str_to_file

MCCQ_QUERY_SYNTAX_HELP: str = "\n".join(
    [
        "```hs",
        "command [-t] [-e] [-c CAPACITY] [-v VERSION]",
        "```",
        "**Positional arguments**",
        "- `command`: The command to query (Supports regex)",
        "**Optional arguments**",
        "- `-t`, `--showtypes`: Whether to show argument types",
        "- `-e`, `--explode`: Whether to expand all subcommands, regardless of capacity",
        "- `-c CAPACITY`, `--capacity CAPACITY`: Maximum number of subcommands to render before collapsing",
        "- `-v VERSION`, `--version VERSION`: Which version(s) to use for the command (repeatable)",
    ]
)
MCCQ_REPO_URL: str = "https://github.com/Arcensoth/mccq"


class MCCQCog(Cog, name="commanderbot.ext.mccq"):
    def __init__(self, bot: Bot, **options):
        self.bot: Bot = bot
        self.log: Logger = getLogger(self.qualified_name)
        self.options = MCCQOptions.from_data(options)

        # Create Java query manager, if configured
        self.java_query_manager: Optional[MCCQManager] = None
        if self.options.java:
            self.java_query_manager = MCCQManager.from_java_options(self.options.java)

        # Create Bedrock query manager, if configured
        self.bedrock_query_manager: Optional[MCCQManager] = None
        if self.options.bedrock:
            self.bedrock_query_manager = MCCQManager.from_bedrock_options(
                self.options.bedrock
            )

    async def cog_load(self):
        self._on_reload_query_managers.start()
        self._on_update_presence.start()

    async def cog_unload(self):
        self._on_reload_query_managers.stop()
        self._on_update_presence.stop()

    def _reload_query_managers(self):
        self.log.info("Reloading query managers...")
        if self.java_query_manager:
            self.java_query_manager.reload()
            self.log.info("Reloaded Java query manager")
        if self.bedrock_query_manager:
            self.bedrock_query_manager.reload()
            self.log.info("Reloaded Bedrock query manager")

    async def _mccq(
        self, query_manager: MCCQManager, interaction: Interaction, query: str
    ):
        # Respond to the interaction with a defer since we may need to do a web request
        await interaction.response.defer()

        # Try to query the command
        try:
            results, wiki_url = await query_manager.query_command(query)
        except Exception as ex:
            await interaction.delete_original_response()
            raise ex

        # Format the message and create the view if necessary
        msg = f"```hs\n{results}\n```"
        view = ui.View()
        if wiki_url:
            view.add_item(ui.Button(label="View on wiki", url=wiki_url))

        # Send message with query results
        if len(msg) <= MAX_MESSAGE_LENGTH:
            await interaction.followup.send(
                msg, view=view, allowed_mentions=AllowedMentions.none()
            )
        # Message is too big, so send it as a file
        else:
            await interaction.followup.send(
                file=str_to_file(results, "results.txt"),
                view=view,
                allowed_mentions=AllowedMentions.none(),
            )

    # @@ TASKS

    # @@ Reload the query managers every hour so the latest version stays up to date
    @tasks.loop(hours=1)
    async def _on_reload_query_managers(self):
        self._reload_query_managers()

    # @@ Temporary hack to update the presence every hour
    async def _get_version_from_file(
        self, session: aiohttp.ClientSession, version_file_url: str
    ) -> Optional[str]:
        async with session.get(version_file_url) as response:
            if response.status == 200:
                return await response.text()

    @tasks.loop(hours=1)
    async def _on_update_presence(self):
        # Return early if the bot presence is configured to be updated
        if not self.options.bot_presence:
            return

        # Get the versions for Java and Bedrock
        self.log.info("Updating bot presence...")
        presence_parts: list[str] = []
        async with aiohttp.ClientSession(headers={"User-Agent": USER_AGENT}) as session:
            # Get latest Java version
            if url := self.options.bot_presence.java_version_file_url:
                if version := await self._get_version_from_file(session, url):
                    presence_parts.append(f"JE {version}")

            # Get latest Bedrock version
            if url := self.options.bot_presence.bedrock_version_file_url:
                if version := await self._get_version_from_file(session, url):
                    presence_parts.append(f"BE {version}")

        # Return early if `presence_parts` is empty
        if not presence_parts:
            self.log.warning(
                "Could not update presence since no Java or Bedrock versions were found"
            )
            return

        presence_text: str = " & ".join(presence_parts)
        activity = Activity(name=presence_text, type=ActivityType.playing)
        await self.bot.change_presence(activity=activity)

        self.log.info(f"Set presence to '{presence_text}'")

    @_on_update_presence.before_loop
    async def _before_on_update_presence(self):
        # Wait for the bot to be ready so an exception isn't thrown when we try updating the presence
        await self.bot.wait_until_ready()

    # @@ COMMANDS

    # @@ mccreload
    @command(name="mccreload", description="Reloads the query managers")
    @guild_only()
    @default_permissions(administrator=True)
    @checks.is_owner()
    async def cmd_mccreload(self, interaction: Interaction):
        self._reload_query_managers()
        await interaction.response.send_message("✅ Reloaded query managers")

    # @@ mcc

    cmd_mcc = Group(name="mcc", description="Query a Minecraft command")

    # @@ mcc help
    @cmd_mcc.command(name="help", description="Show the query syntax")
    async def cmd_mcc_help(self, interaction: Interaction):
        embed = Embed(
            title="How to format your Minecraft command query",
            description=MCCQ_QUERY_SYNTAX_HELP,
            color=0x00ACED,
        )
        view = ui.View()
        view.add_item(ui.Button(label="Learn more", url=MCCQ_REPO_URL))
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    # @@ mcc java
    @cmd_mcc.command(name="java", description="Query a Minecraft: Java Edition command")
    @describe(query="The command to query (Run '/mcc help' for the query syntax)")
    async def cmd_mcc_java(self, interaction: Interaction, query: str):
        # Throw an exception if the Java query manager hasn't been configured
        if not self.java_query_manager:
            raise JavaQueryManagerNotConfigured
        await self._mccq(self.java_query_manager, interaction, query)

    # @@ mcc bedrock
    @cmd_mcc.command(
        name="bedrock", description="Query a Minecraft: Bedrock Edition command"
    )
    @describe(query="The command to query (Run '/mcc help' for the query syntax)")
    async def cmd_mcc_bedrock(self, interaction: Interaction, query: str):
        # Throw an exception if the Bedrock query manager hasn't been configured
        if not self.bedrock_query_manager:
            raise BedrockQueryManagerNotConfigured
        await self._mccq(self.bedrock_query_manager, interaction, query)
