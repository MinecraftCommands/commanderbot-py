import re

from discord import Embed, Interaction, ui
from discord.app_commands import (
    Transform,
    Transformer,
    allowed_installs,
    command,
    describe,
)
from discord.ext.commands import Bot, Cog
from discord.utils import format_dt

from commanderbot.ext.jira.jira_client import JiraClient
from commanderbot.ext.jira.jira_exceptions import InvalidIssueFormat
from commanderbot.ext.jira.jira_options import JiraOptions
from commanderbot.ext.jira.jira_utils import JiraIssue, JiraQuery
from commanderbot.lib import constants

JIRA_URL_PATTERN = re.compile(r"^https?://[^/]+.*?(\w+)-(\d+)")
JIRA_ISSUE_ID_PATTERN = re.compile(r"^(\w+)-(\d+)")


class JiraQueryTransformer(Transformer):
    """
    A transformer that creates a `JiraQuery` from an issue ID or URL
    """

    async def transform(self, interaction: Interaction, value: str) -> JiraQuery:
        # Throw away any request parameters
        raw_query: str = value.split("?")[0]

        # Parse argument
        if matches := JIRA_URL_PATTERN.match(raw_query):
            project, id = matches.groups()
            return JiraQuery(project.upper(), int(id), f"{project.upper()}-{int(id)}")
        elif matches := JIRA_ISSUE_ID_PATTERN.match(raw_query):
            project, id = matches.groups()
            return JiraQuery(project.upper(), int(id), f"{project.upper()}-{int(id)}")
        else:
            raise InvalidIssueFormat


class JiraCog(Cog, name="commanderbot.ext.jira"):
    def __init__(self, bot: Bot, **options):
        self.bot: Bot = bot
        self.options = JiraOptions.from_data(options)
        self.jira_client = JiraClient.from_options(self.options)

    @command(name="jira", description="Query an issue from Jira")
    @describe(query="The issue ID or URL to query")
    @allowed_installs(guilds=True, users=True)
    async def cmd_jira(
        self,
        interaction: Interaction,
        query: Transform[JiraQuery, JiraQueryTransformer],
    ):
        # Respond to the interaction with a defer since the web request may take a while
        await interaction.response.defer()

        # Try to get the issue
        try:
            issue: JiraIssue = await self.jira_client.get_issue(query)
        except Exception as ex:
            await interaction.delete_original_response()
            raise ex

        # Create embed title and limit it to 256 characters
        title: str = f"[{issue.issue_id}] {issue.summary}"
        if len(title) > constants.MAX_EMBED_TITLE_LENGTH:
            title = f"{title[:253]}..."

        # Create issue embed
        issue_embed: Embed = Embed(
            title=title,
            url=issue.url,
            color=issue.status_color.value,
        )
        issue_embed.set_thumbnail(url=self.options.icon_url)
        issue_embed.add_field(name="Created", value=format_dt(issue.created, "R"))
        issue_embed.add_field(name="Updated", value=format_dt(issue.updated, "R"))
        issue_embed.add_field(name="Since Version", value=issue.since_version)
        issue_embed.add_field(name="Fix Version", value=issue.fix_version)
        issue_embed.add_field(
            name="Confirmation Status", value=issue.confirmation_status
        )
        issue_embed.add_field(name="Status", value=issue.status)
        issue_embed.add_field(name="Resolution", value=issue.resolution)
        issue_embed.add_field(name="Mojang Priority", value=issue.mojang_priority)
        issue_embed.add_field(name="Votes", value=issue.votes)

        # Create view with link button
        jira_link_button: ui.View = ui.View()
        jira_link_button.add_item(ui.Button(label="View on Jira", url=issue.url))

        # Send the followup message with the issue embed and link button
        await interaction.followup.send(embed=issue_embed, view=jira_link_button)
