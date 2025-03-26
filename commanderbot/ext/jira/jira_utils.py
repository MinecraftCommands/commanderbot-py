from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Literal

type CustomFieldKeys = Literal["votes", "confirmation_status", "mojang_priority"]
type CustomFields = dict[CustomFieldKeys, str]


@dataclass
class JiraQuery:
    project: str
    id: int
    issue_id: str


class StatusColor(Enum):
    UNKNOWN = 0x00ACED

    MEDIUM_GRAY = 0x42526E
    BLUE_GRAY = 0x42526E
    DEFAULT = 0x42526E

    GREEN = 0x00875A
    SUCCESS = 0x00875A

    YELLOW = 0x0052CC
    INPROGRESS = 0x0052CC

    WARM_RED = 0xDE350B
    REMOVED = 0xDE350B

    BROWN = 0xFF991F
    MOVED = 0xFF991F

    @classmethod
    def from_str(cls, color: str):
        color = color.replace("-", "_").upper()
        try:
            return cls[color]
        except KeyError:
            return cls.UNKNOWN


@dataclass
class JiraIssue:
    issue_id: str
    url: str

    # Default fields
    summary: str
    created: datetime
    updated: datetime
    status: str
    status_color: StatusColor
    resolution: str
    since_version: str
    fix_version: str
    watching: int

    # Custom fields
    votes: int
    confirmation_status: str
    mojang_priority: str
