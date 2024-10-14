import json
from dataclasses import dataclass, field
from logging import Logger, getLogger
from pathlib import Path
from typing import Any, Optional, Self

import discord

from commanderbot.core.configured_extension import ConfiguredExtension
from commanderbot.core.exceptions import ExtensionNotInConfig
from commanderbot.lib import AllowedMentions, FromDataMixin, Intents
from commanderbot.lib.types import JsonObject


@dataclass
class Config(FromDataMixin):
    command_prefix: str
    intents: discord.Intents
    allowed_mentions: discord.AllowedMentions

    extensions: dict[str, ConfiguredExtension]
    enabled_extensions: list[ConfiguredExtension] = field(
        init=False, default_factory=list
    )
    disabled_extensions: list[ConfiguredExtension] = field(
        init=False, default_factory=list
    )

    @classmethod
    def try_from_data(cls, data: Any) -> Optional[Self]:
        if isinstance(data, dict):
            log: Logger = getLogger(__name__)
            log.info(f"Number of configuration keys: {len(data)}")

            # Get command prefix
            command_prefix: str = data["command_prefix"]
            log.info(f"Command prefix: {command_prefix}")

            # Process intents
            intents = Intents.default()
            if i := Intents.from_field_optional(data, "intents"):
                intents = Intents.default() & i
            if i := Intents.from_field_optional(data, "privileged_intents"):
                intents |= Intents.privileged() & i

            log.info(f"Using intents flags: {intents.value}")

            # Process allowed mentions
            allowed_mentions = AllowedMentions.not_everyone()
            if m := AllowedMentions.from_field_optional(data, "allowed_mentions"):
                allowed_mentions = m

            log.info(f"Using allowed mentions: {allowed_mentions.to_json()}")

            # Process extensions
            log.info("Processing extensions...")

            raw_extensions = data.get("extensions", [])
            extensions: dict[str, ConfiguredExtension] = {}
            for raw_entry in raw_extensions:
                ext = ConfiguredExtension.from_data(raw_entry)
                extensions[ext.name] = ext

            if extensions:
                log.info(f"Processed {len(extensions)} extensions...")
            else:
                log.warning("No extensions configured.")

            return cls(
                command_prefix=command_prefix,
                intents=intents,
                allowed_mentions=allowed_mentions,
                extensions=extensions,
            )

    @classmethod
    def from_file(cls, path: Path) -> Self:
        raw_config: JsonObject = {}
        with open(path) as file:
            raw_config = json.load(file)

        return cls.from_data(raw_config)

    def __post_init__(self):
        self._rebuild_extension_states()

    def _rebuild_extension_states(self):
        self.enabled_extensions.clear()
        self.disabled_extensions.clear()

        for ext in self.extensions.values():
            if ext.disabled:
                self.disabled_extensions.append(ext)
            else:
                self.enabled_extensions.append(ext)

    def require_extension(self, name: str) -> ConfiguredExtension:
        if ext := self.extensions.get(name):
            return ext
        raise ExtensionNotInConfig(name)

    def enable_extension(self, name: str):
        ext: ConfiguredExtension = self.require_extension(name)
        if ext.disabled:
            ext.disabled = False
            self._rebuild_extension_states()

    def disable_extension(self, name: str):
        ext: ConfiguredExtension = self.require_extension(name)
        if not ext.disabled:
            ext.disabled = True
            self._rebuild_extension_states()

    def get_extension_options(self, name: str) -> Optional[JsonObject]:
        if ext := self.extensions.get(name):
            return ext.options
