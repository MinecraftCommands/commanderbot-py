from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import aiohttp

from commanderbot.ext.jira.jira_exceptions import (
    ConnectionError,
    InvalidURL,
    IssueHasNoFields,
    IssueNotFound,
    RequestError,
)
from commanderbot.ext.jira.jira_issue import JiraIssue, StatusColor
from commanderbot.lib import constants


@dataclass
class JiraQuery:
    base_url: Optional[str]
    issue_id: str


class JiraClient:
    def __init__(self, url: Optional[str]):
        self.url: Optional[str] = url

    async def _request_issue_data(self, base_url: str, issue_id: str) -> dict:
        try:
            issue_url: str = f"{base_url}/api/jql-search-post"
            headers: dict[str, str] = {"User-Agent": constants.USER_AGENT}
            project = issue_id.split('-')[0]
            body = {
              "advanced": True,
              "search": f"key = {issue_id}",
              "project": project
            }
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    issue_url, json=body, headers=headers, raise_for_status=True
                ) as response:
                    data = await response.json()
                    issue = data["issues"][0]
                    return issue

        except aiohttp.InvalidURL:
            raise InvalidURL(issue_id)

        except aiohttp.ClientConnectorError:
            raise ConnectionError(base_url)

        except aiohttp.ClientResponseError:
            raise IssueNotFound(issue_id)

        except aiohttp.ClientError:
            raise RequestError(issue_id)

    async def get_issue(self, query: JiraQuery) -> JiraIssue:
        # Request issue data and get its fields
        base_url: str = query.base_url or self.url or ""
        issue_id: str = query.issue_id

        data: dict = await self._request_issue_data(base_url, issue_id)
        fields: dict = data.get("fields", {})
        if not fields:
            raise IssueHasNoFields(issue_id)

        # Extract data from fields and construct an issue
        assignee: str = "Unassigned"
        if user := fields.get("assignee"):
            assignee = user["displayName"]

        resolution: str = "Unresolved"
        if res := fields.get("resolution"):
            resolution = res["name"]

        since_version: str = "None"
        if ver := fields.get("versions"):
            since_version = ver[0]["name"]

        fix_version: str = "None"
        if ver := fields.get("fixVersions"):
            fix_version = ver[-1]["name"]

        return JiraIssue(
            issue_id=issue_id,
            url=f"{base_url}/browse/{issue_id}",
            icon_url=f"{base_url}/jira-favicon-hires.png",
            summary=fields["summary"],
            reporter=fields["reporter"]["displayName"],
            assignee=assignee,
            created=datetime.strptime(fields["created"], "%Y-%m-%dT%H:%M:%S.%f%z"),
            updated=datetime.strptime(fields["updated"], "%Y-%m-%dT%H:%M:%S.%f%z"),
            status=fields["status"]["name"],
            status_color=StatusColor.from_str(
                fields["status"]["statusCategory"]["colorName"]
            ),
            resolution=resolution,
            since_version=since_version,
            fix_version=fix_version,
            votes=fields["votes"]["votes"],
        )
