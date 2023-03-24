from discord.app_commands import AppCommandError

from commanderbot.lib import ResponsiveException


class JiraException(ResponsiveException):
    pass


class JiraTransformerException(ResponsiveException, AppCommandError):
    pass


class IssueNotFound(JiraException):
    def __init__(self, issue_id: str):
        self.issue_id = issue_id
        super().__init__(f"😬 `{self.issue_id}` does not exist or it may be private")


class IssueHasNoFields(JiraException):
    def __init__(self, issue_id: str):
        self.issue_id = issue_id
        super().__init__(f"😬 `{self.issue_id}` does not have any fields")


class ConnectionError(JiraException):
    def __init__(self, url: str):
        self.url = url
        super().__init__(f"😵 Could not connect to `{self.url}`")


class RequestError(JiraException):
    def __init__(self, issue_id: str):
        self.issue_id = issue_id
        super().__init__(f"😵 There was an error while requesting `{self.issue_id}`")


class InvalidIssueFormat(JiraTransformerException):
    def __init__(self):
        super().__init__(
            "😬 Jira issues must use the `<project>-<id>` format or be a URL"
        )
