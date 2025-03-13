import re
from datetime import datetime
from typing import AsyncIterable, Optional, Protocol

from discord import Guild

from commanderbot.lib import ChannelID, UserID


class FridayRule(Protocol):
    name: str
    pattern: Optional[re.Pattern]
    chance: float
    cooldown: int
    response: str
    last_response: Optional[datetime]
    hits: int
    added_by_id: UserID
    modified_by_id: UserID
    added_on: datetime
    modified_on: datetime

    @property
    def available(self) -> bool: ...

    @property
    def avaliable_after(self) -> Optional[datetime]: ...

    def modify(
        self,
        pattern: Optional[re.Pattern],
        chance: float,
        cooldown: int,
        response: str,
        user_id: UserID,
    ): ...

    def check(self, content: str) -> bool: ...


class FridayStore(Protocol):
    """
    Abstracts the data storage and persistence of the friday cog.
    """

    async def is_channel_registered(
        self, guild: Guild, channel_id: ChannelID
    ) -> bool: ...

    async def register_channel(self, guild: Guild, channel_id: ChannelID): ...

    async def unregister_channel(self, guild: Guild, channel_id: ChannelID): ...

    async def require_rule(self, guild: Guild, name: str) -> FridayRule: ...

    async def add_rule(
        self,
        guild: Guild,
        name: str,
        pattern: Optional[str],
        chance: float,
        cooldown: int,
        response: str,
        user_id: UserID,
    ) -> FridayRule: ...

    async def modify_rule(
        self,
        guild: Guild,
        name: str,
        pattern: Optional[str],
        chance: float,
        cooldown: int,
        response: str,
        user_id: UserID,
    ) -> FridayRule: ...

    async def remove_rule(self, guild: Guild, name: str) -> FridayRule: ...

    async def check_rules(self, guild: Guild, content: str) -> Optional[FridayRule]: ...

    async def update_on_rule_matched(self, rule: FridayRule): ...

    def get_rules(
        self,
        guild: Guild,
        *,
        rule_filter: Optional[str] = None,
        case_sensitive: bool = False,
        sort: bool = False,
        cap: Optional[int] = None,
    ) -> AsyncIterable[FridayRule]: ...
