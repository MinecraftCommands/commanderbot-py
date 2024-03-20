from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Literal, Optional, Protocol, Self

from commanderbot.lib import FromDataMixin

__all__ = ("FeedProvider", "FeedProviderOptions", "MissingFeedHandler")


class MissingFeedHandler(Exception):
    def __init__(self):
        super().__init__("A valid feed handler couldn't be found or it wasn't assigned")


class FeedProvider(Protocol):
    url: str
    prev_status_code: Optional[int]
    prev_request_date: Optional[datetime]
    next_request_date: Optional[datetime]

    def start(self): ...
    def stop(self): ...
    def restart(self): ...


class FeedProviderOptions(Protocol):
    feed_url: str
    feed_icon_url: str

    cache_size: int


@dataclass
class RSSFeedItem(FromDataMixin):
    """
    Represents a mostly complete RSS feed item.
    A few nonstandard elements are supported.
    """

    id: Optional[str]
    link: str
    title: str
    description: str
    published: datetime

    # Nonstandard RSS feed item elements
    primary_tag: Optional[str] = None
    image_url: Optional[str] = None

    # @overrides FromDataMixin
    @classmethod
    def try_from_data(cls, data: Any) -> Optional[Self]:
        if isinstance(data, dict):
            # `struct_time` 9 tuple
            st = data["published_parsed"]
            return cls(
                id=data.get("id"),
                link=data["link"],
                title=data["title"],
                description=data["summary"],
                published=datetime(*(st[:6]), tzinfo=timezone.utc),
                primary_tag=data.get("primarytag"),
                image_url=data.get("imageurl"),
            )


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
