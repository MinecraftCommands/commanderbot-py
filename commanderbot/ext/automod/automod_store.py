from typing import AsyncIterable, Optional, Protocol, Type, TypeVar

from discord import Guild

from commanderbot.ext.automod.automod_bucket import AutomodBucket
from commanderbot.ext.automod.automod_event import AutomodEvent
from commanderbot.ext.automod.automod_rule import AutomodRule
from commanderbot.lib import JsonObject, LogOptions, RoleSet

BT = TypeVar("BT", bound=AutomodBucket)


class AutomodStore(Protocol):
    """
    Abstracts the data storage and persistence of the automod cog.
    """

    async def get_default_log_options(self, guild: Guild) -> Optional[LogOptions]:
        ...

    async def set_default_log_options(
        self, guild: Guild, log_options: Optional[LogOptions]
    ) -> Optional[LogOptions]:
        ...

    async def get_permitted_roles(self, guild: Guild) -> Optional[RoleSet]:
        ...

    async def set_permitted_roles(
        self, guild: Guild, permitted_roles: Optional[RoleSet]
    ) -> Optional[RoleSet]:
        ...

    def all_rules(self, guild: Guild) -> AsyncIterable[AutomodRule]:
        ...

    def rules_for_event(
        self, guild: Guild, event: AutomodEvent
    ) -> AsyncIterable[AutomodRule]:
        ...

    def query_rules(self, guild: Guild, query: str) -> AsyncIterable[AutomodRule]:
        ...

    async def get_rule(self, guild: Guild, name: str) -> Optional[AutomodRule]:
        ...

    async def require_rule(self, guild: Guild, name: str) -> AutomodRule:
        ...

    async def add_rule(self, guild: Guild, data: JsonObject) -> AutomodRule:
        ...

    async def remove_rule(self, guild: Guild, name: str) -> AutomodRule:
        ...

    async def modify_rule(
        self, guild: Guild, name: str, data: JsonObject
    ) -> AutomodRule:
        ...

    async def enable_rule(self, guild: Guild, name: str) -> AutomodRule:
        ...

    async def disable_rule(self, guild: Guild, name: str) -> AutomodRule:
        ...

    async def increment_rule_hits(self, guild: Guild, name: str) -> AutomodRule:
        ...

    async def get_bucket(
        self, guild: Guild, name: str, bucket_type: Type[BT]
    ) -> Optional[BT]:
        ...

    async def require_bucket(
        self, guild: Guild, name: str, bucket_type: Type[BT]
    ) -> BT:
        ...
