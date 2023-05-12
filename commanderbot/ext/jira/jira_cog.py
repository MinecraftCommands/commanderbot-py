import re
from logging import Logger, getLogger

from discord import Embed, Interaction, ui
from discord.app_commands import Transform, Transformer, command, describe
from discord.ext.commands import Bot, Cog

from commanderbot.ext.jira.jira_client import JiraClient, JiraQuery
from commanderbot.ext.jira.jira_exceptions import InvalidIssueFormat
from commanderbot.ext.jira.jira_issue import JiraIssue

JIRA_URL_PATTERN = re.compile(r"^(https?://[^/]+).*?(\w+)-(\d+)")
JIRA_ISSUE_ID_PATTERN = re.compile(r"^(\w+)-(\d+)")


class JiraQueryTransformer(Transformer):
    """
    A transformer that creates a `JiraQuery` from an issue ID or URL
    """

    async def transform(self, interaction: Interaction, value: str) -> JiraQuery:
        # Throw away any request parameters
        raw_query: str = value.split("?")[0]
        if matches := JIRA_URL_PATTERN.match(raw_query):
            base_url, project, id = matches.groups()
            return JiraQuery(base_url, f"{project.upper()}-{int(id)}")
        elif matches := JIRA_ISSUE_ID_PATTERN.match(raw_query):
            project, id = matches.groups()
            return JiraQuery(None, f"{project.upper()}-{int(id)}")
        else:
            raise InvalidIssueFormat


class JiraCog(Cog, name="commanderbot.ext.jira"):
    def __init__(self, bot: Bot, **options):
        self.bot: Bot = bot
        self.log: Logger = getLogger(self.qualified_name)

        # Get the URL from the config
        url = options.get("url", "")
        if not url:
            # Log an error if the URL doesn't exist
            self.log.error("No Jira URL was given in the bot config")

        # Create the Jira client
        self.jira_client: JiraClient = JiraClient(url)

    @command(name="jira", description="Query a Jira issue")
    @describe(query="The issue ID or URL to query")
    async def cmd_jira(
        self,
        interaction: Interaction,
        query: Transform[JiraQuery, JiraQueryTransformer],
    ):
        # Repond to the interaction with a defer since the web request may take a while
        await interaction.response.defer()

        # Try to get the issue
        try:
            issue: JiraIssue = await self.jira_client.get_issue(query)
        except Exception as ex:
            await interaction.delete_original_response()
            raise ex

        # Create embed title and limit it to 256 characters
        title: str = f"[{issue.issue_id}] {issue.summary}"
        if len(title) > 256:
            title = f"{title[:253]}..."

        # Create issue embed
        issue_embed: Embed = Embed(
            title=title,
            url=issue.url,
            color=issue.status_color.value,
        )

        issue_embed.set_thumbnail(url=issue.icon_url)

        for k, v in issue.fields.items():
            issue_embed.add_field(name=k, value=v)

        # Create view with link button
        jira_link_button: ui.View = ui.View()
        jira_link_button.add_item(ui.Button(label="View on Jira", url=issue.url))

        # Send the followup message with the issue embed and link button
        await interaction.followup.send(embed=issue_embed, view=jira_link_button)
