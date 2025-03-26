from dataclasses import dataclass
from typing import Any, Optional, Self

from commanderbot.ext.jira.jira_utils import CustomFields
from commanderbot.lib import FromDataMixin


@dataclass
class JiraOptions(FromDataMixin):
    base_url: str
    icon_url: str
    custom_fields: CustomFields

    # @implements FromDataMixin
    @classmethod
    def try_from_data(cls, data: Any) -> Optional[Self]:
        if isinstance(data, dict):
            return cls(
                base_url=data["base_url"],
                icon_url=data["icon_url"],
                custom_fields=data.get("custom_fields", {}),
            )
