from dataclasses import dataclass, field
from typing import Any, Optional, Self

from commanderbot.ext.feeds.providers import (
    MinecraftBedrockUpdatesOptions,
    MinecraftJavaUpdatesOptions,
)
from commanderbot.lib import FromDataMixin
from commanderbot.lib.cogs.database import (
    DatabaseOptions,
    InMemoryDatabaseOptions,
    make_database_options,
)


@dataclass
class FeedsOptions(FromDataMixin):
    minecraft_java_updates: MinecraftJavaUpdatesOptions
    minecraft_bedrock_updates: MinecraftBedrockUpdatesOptions

    database: DatabaseOptions = field(default_factory=InMemoryDatabaseOptions)

    # @overrides FromDataMixin
    @classmethod
    def try_from_data(cls, data: Any) -> Optional[Self]:
        if isinstance(data, dict):
            minecraft_java_updates = MinecraftJavaUpdatesOptions.from_data(
                data["minecraft_java_updates"]
            )
            minecraft_bedrock_updates = MinecraftBedrockUpdatesOptions.from_data(
                data["minecraft_bedrock_updates"]
            )
            database_options = make_database_options(data.get("database"))
            return cls(
                minecraft_java_updates=minecraft_java_updates,
                minecraft_bedrock_updates=minecraft_bedrock_updates,
                database=database_options,
            )
