from discord.app_commands import AppCommandError

from commanderbot.lib import ResponsiveException


class JiraException(ResponsiveException):
    pass


class JiraTransformerException(ResponsiveException, AppCommandError):
    pass


class InvalidURL(JiraException):
    def __init__(self, issue_id: str):
        self.issue_id: str = issue_id
        super().__init__(f"😵 Unable to request `{self.issue_id}` from an invalid URL")


class ConnectionError(JiraException):
    def __init__(self, url: str):
        self.url: str = url
        super().__init__(f"😵 Could not connect to `{self.url}`")


class IssueNotFound(JiraException):
    def __init__(self, issue_id: str):
        self.issue_id: str = issue_id
        super().__init__(f"😬 `{self.issue_id}` does not exist or it may be private")


class RequestError(JiraException):
    def __init__(self, issue_id: str):
        self.issue_id: str = issue_id
        super().__init__(f"😵 An error occurred while requesting `{self.issue_id}`")


class InvalidIssueFormat(JiraTransformerException):
    def __init__(self):
        super().__init__(
            "😬 Jira issues must use the `<project>-<id>` format or be a valid Jira URL"
        )
