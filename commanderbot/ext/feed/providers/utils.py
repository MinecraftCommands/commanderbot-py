from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional, Self

from commanderbot.lib import FromDataMixin


class MissingHandler(Exception):
    def __init__(self, provider_name: str, reason: str):
        self.provider_name: str = provider_name
        self.reason: str = reason
        super().__init__(
            f"Missing handler for {self.provider_name} due to: {self.reason}"
        )


@dataclass
class ZendeskArticle(FromDataMixin):
    id: int
    section_id: int
    url: str
    html_url: str
    title: str
    name: str
    created_at: datetime
    updated_at: datetime
    edited_at: datetime
    body: str

    # @overrides FromDataMixin
    @classmethod
    def try_from_data(cls, data: Any) -> Optional[Self]:
        if isinstance(data, dict):
            return cls(
                id=data["id"],
                section_id=data["section_id"],
                url=data["url"],
                html_url=data["html_url"],
                title=data["title"],
                name=data["name"],
                created_at=datetime.strptime(data["created_at"], "%Y-%m-%dT%H:%M:%SZ"),
                updated_at=datetime.strptime(data["updated_at"], "%Y-%m-%dT%H:%M:%SZ"),
                edited_at=datetime.strptime(data["edited_at"], "%Y-%m-%dT%H:%M:%SZ"),
                body=data["body"],
            )
