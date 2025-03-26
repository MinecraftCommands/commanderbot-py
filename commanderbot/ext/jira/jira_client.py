from datetime import datetime, timezone
from typing import Self

import aiohttp

from commanderbot.ext.jira.jira_exceptions import (
    ConnectionError,
    InvalidURL,
    IssueNotFound,
    RequestError,
)
from commanderbot.ext.jira.jira_options import JiraOptions
from commanderbot.ext.jira.jira_utils import (
    CustomFields,
    JiraIssue,
    JiraQuery,
    StatusColor,
)
from commanderbot.lib import JsonObject, constants


class JiraClient:
    def __init__(self, base_url: str, custom_fields: CustomFields):
        self.base_url: str = base_url
        self.custom_fields: CustomFields = custom_fields

    @classmethod
    def from_options(cls, options: JiraOptions) -> Self:
        return cls(base_url=options.base_url, custom_fields=options.custom_fields)

    async def _fetch_issue_json(self, query: JiraQuery) -> JsonObject:
        try:
            async with aiohttp.ClientSession(
                headers={"User-Agent": constants.USER_AGENT},
                raise_for_status=True,
            ) as session:
                async with session.post(
                    f"{self.base_url}/api/jql-search-post",
                    json={
                        "advanced": True,
                        "search": f"key = '{query.issue_id}'",
                        "project": query.project,
                        "maxResults": 1,
                    },
                    headers={"Content-Type": "application/json"},
                ) as response:
                    return await response.json()
        except aiohttp.InvalidURL:
            raise InvalidURL(query.issue_id)
        except aiohttp.ClientConnectorError:
            raise ConnectionError(self.base_url)
        except aiohttp.ClientResponseError:
            raise IssueNotFound(query.issue_id)
        except aiohttp.ClientError:
            raise RequestError(query.issue_id)

    async def get_issue(self, query: JiraQuery) -> JiraIssue:
        # Fetch issue and raise an exception we got no results
        data: JsonObject = await self._fetch_issue_json(query)
        if data["total"] != 1:
            raise IssueNotFound(query.issue_id)

        # Extract the issue's fields
        issue: JsonObject = data["issues"][0]
        fields: JsonObject = issue["fields"]

        # Extract data from default fields
        resolution: str = "Unresolved"
        if field_data := fields.get("resolution"):
            resolution = field_data["name"]

        since_version: str = "None"
        if field_data := fields.get("versions"):
            since_version = field_data[0]["name"]

        fix_version: str = "None"
        if field_data := fields.get("fixVersions"):
            fix_version = field_data[-1]["name"]

        # Extract data from custom fields
        votes: int = 0
        if field_name := self.custom_fields.get("votes"):
            if field_data := fields.get(field_name):
                votes = int(field_data)

        confirmation_status: str = "Unconfirmed"
        if field_name := self.custom_fields.get("confirmation_status"):
            if field_data := fields.get(field_name):
                confirmation_status = field_data.get("value")

        mojang_priority: str = "None"
        if field_name := self.custom_fields.get("mojang_priority"):
            if field_data := fields.get(field_name):
                mojang_priority = field_data.get("value")

        # Create Jira issue
        return JiraIssue(
            issue_id=query.issue_id,
            url=f"{self.base_url}/browse/{query.project}/issues/{query.issue_id}",
            summary=fields["summary"],
            created=datetime.fromisoformat(fields["created"]).replace(
                tzinfo=timezone.utc
            ),
            updated=datetime.fromisoformat(fields["updated"]).replace(
                tzinfo=timezone.utc
            ),
            status=fields["status"]["name"],
            status_color=StatusColor.from_str(
                fields["status"]["statusCategory"]["colorName"]
            ),
            resolution=resolution,
            since_version=since_version,
            fix_version=fix_version,
            watching=fields["watches"]["watchCount"],
            votes=votes,
            confirmation_status=confirmation_status,
            mojang_priority=mojang_priority,
        )
