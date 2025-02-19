from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from discord.utils import format_dt


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
    summary: str
    assignee: str
    created: datetime
    updated: datetime
    status: str
    status_color: StatusColor
    resolution: str
    since_version: str
    fix_version: str
    votes: int

    @property
    def fields(self) -> dict:
        return {
            "Assigned To": self.assignee,
            "Created": format_dt(self.created, style="R"),
            "Updated": format_dt(self.updated, style="R"),
            "Since Version": self.since_version,
            "Fix Version": self.fix_version,
            "Status": self.status,
            "Resolution": self.resolution,
            "Votes": self.votes,
        }
