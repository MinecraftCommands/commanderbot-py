from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Coroutine, Literal, Optional, Self

from commanderbot.lib import FromDataMixin

type FeedHandler[T] = Callable[[T], Coroutine[Any, Any, None]]


@dataclass
class MinecraftJavaChangelog(FromDataMixin):
    """
    Represents a complete changelog from the launcher for Minecraft: Java Edition
    """

    id: str
    version: str
    type: Literal["release", "snapshot"]
    title: str
    short_text: str
    image_title: str
    image_url: str
    date: datetime
    date_utc: datetime
    content_url: str

    # @implements FromDataMixin
    @classmethod
    def try_from_data(cls, data: Any) -> Optional[Self]:
        if isinstance(data, dict):
            date = datetime.strptime(data["date"], "%Y-%m-%dT%H:%M:%S.%fZ")
            return cls(
                id=data["id"],
                version=data["version"],
                type=data["type"],
                title=data["title"],
                short_text=data["shortText"],
                image_title=data["image"]["title"],
                image_url=data["image"]["url"],
                date=date,
                date_utc=date.astimezone(timezone.utc),
                content_url=data["contentPath"],
            )

    @property
    def is_release(self) -> bool:
        return self.type == "release"

    @property
    def is_snapshot(self) -> bool:
        return self.type == "snapshot"


@dataclass
class MinecraftJavaVersion(FromDataMixin):
    """
    Represents a mostly complete version from the Minecraft: Java Edition
    version manifest with some slight restructuring.
    """

    id: str
    type: Literal["release", "snapshot", "old_alpha", "old_beta"]
    time: datetime
    release_time: datetime
    release_time_utc: datetime
    java_version: int
    client_jar_url: str
    server_jar_url: str
    client_mappings_url: Optional[str]
    server_mappings_url: Optional[str]

    url: Optional[str] = None

    # @implements FromDataMixin
    @classmethod
    def try_from_data(cls, data: Any) -> Optional[Self]:
        if isinstance(data, dict):
            release_time = datetime.fromisoformat(data["releaseTime"])
            client_mappings_url = (
                data["downloads"].get("client_mappings", {}).get("url")
            )
            server_mappings_url = (
                data["downloads"].get("server_mappings", {}).get("url")
            )
            return cls(
                id=data["id"],
                type=data["type"],
                time=datetime.fromisoformat(data["time"]),
                release_time=release_time,
                release_time_utc=release_time.astimezone(timezone.utc),
                java_version=data["javaVersion"]["majorVersion"],
                client_jar_url=data["downloads"]["client"]["url"],
                server_jar_url=data["downloads"]["server"]["url"],
                client_mappings_url=client_mappings_url,
                server_mappings_url=server_mappings_url,
            )

    @property
    def is_release(self) -> bool:
        return self.type == "release"

    @property
    def is_snapshot(self) -> bool:
        return self.type == "snapshot"

    @property
    def is_old_beta(self) -> bool:
        return self.type == "old_beta"

    @property
    def is_old_alpha(self) -> bool:
        return self.type == "old_alpha"


@dataclass
class ZendeskArticle(FromDataMixin):
    """
    Represents a mostly complete Zendesk article.
    """

    id: int
    section_id: int
    url: str
    html_url: str
    title: str
    name: str
    created_at: datetime
    updated_at: datetime
    edited_at: datetime
    created_at_utc: datetime
    updated_at_utc: datetime
    edited_at_utc: datetime
    body: str

    # @implements FromDataMixin
    @classmethod
    def try_from_data(cls, data: Any) -> Optional[Self]:
        if isinstance(data, dict):
            created_at = datetime.strptime(data["created_at"], "%Y-%m-%dT%H:%M:%SZ")
            updated_at = datetime.strptime(data["updated_at"], "%Y-%m-%dT%H:%M:%SZ")
            edited_at = datetime.strptime(data["edited_at"], "%Y-%m-%dT%H:%M:%SZ")
            return cls(
                id=data["id"],
                section_id=data["section_id"],
                url=data["url"],
                html_url=data["html_url"],
                title=data["title"],
                name=data["name"],
                created_at=created_at,
                updated_at=updated_at,
                edited_at=edited_at,
                created_at_utc=created_at.astimezone(timezone.utc),
                updated_at_utc=updated_at.astimezone(timezone.utc),
                edited_at_utc=edited_at.astimezone(timezone.utc),
                body=data["body"],
            )
