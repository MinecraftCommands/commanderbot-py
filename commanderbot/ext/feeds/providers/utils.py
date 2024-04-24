from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Coroutine, Literal, Optional, Self, TypeAlias, TypeVar

from commanderbot.lib import FromDataMixin

T = TypeVar("T")
FeedHandler: TypeAlias = Callable[[T], Coroutine[Any, Any, None]]


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
    content_url: str

    # @overrides FromDataMixin
    @classmethod
    def try_from_data(cls, data: Any) -> Optional[Self]:
        if isinstance(data, dict):
            return cls(
                id=data["id"],
                version=data["version"],
                type=data["type"],
                title=data["title"],
                short_text=data["shortText"],
                image_title=data["image"]["title"],
                image_url=data["image"]["url"],
                date=datetime.strptime(data["date"], "%Y-%m-%dT%H:%M:%S.%fZ"),
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
    java_version: int
    client_jar_url: str
    server_jar_url: str
    client_mappings_url: str
    server_mappings_url: str

    url: Optional[str] = None

    # @overrides FromDataMixin
    @classmethod
    def try_from_data(cls, data: Any) -> Optional[Self]:
        if isinstance(data, dict):
            return cls(
                id=data["id"],
                type=data["type"],
                time=datetime.fromisoformat(data["time"]),
                release_time=datetime.fromisoformat(data["releaseTime"]),
                java_version=data["javaVersion"]["majorVersion"],
                client_jar_url=data["downloads"]["client"]["url"],
                server_jar_url=data["downloads"]["server"]["url"],
                client_mappings_url=data["downloads"]["client_mappings"]["url"],
                server_mappings_url=data["downloads"]["server_mappings"]["url"],
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
