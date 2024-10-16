import json
from dataclasses import dataclass, field
from logging import Logger, getLogger
from pathlib import Path
from typing import Any, Optional, Self

from commanderbot.core.configured_extension import ConfiguredExtension
from commanderbot.core.exceptions import ExtensionIsRequired, ExtensionNotInConfig
from commanderbot.lib import (
    AllowedMentions,
    FromDataMixin,
    Intents,
    JsonSerializable,
    utils,
)
from commanderbot.lib.types import JsonObject


@dataclass
class Config(JsonSerializable, FromDataMixin):
    command_prefix: str
    intents: Intents
    allowed_mentions: AllowedMentions

    extensions: dict[str, ConfiguredExtension]
    enabled_extensions: list[ConfiguredExtension] = field(
        init=False, default_factory=list
    )
    disabled_extensions: list[ConfiguredExtension] = field(
        init=False, default_factory=list
    )

    # @implements FromDataMixin
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

    # @implements JsonSerializable
    def to_json(self) -> Any:
        intents: Optional[Intents] = Intents.default() & self.intents
        privileged_intents: Intents = Intents.privileged() & self.intents

        # `intents` is an optional field in the config and defaults to `Intents.default()`.
        # So don't include it if it's value is the same as `Intents.default()`.
        if intents == Intents.default():
            intents = None

        # `allowed_mentions` is an optional field in the config and defaults to `AllowedMentions.not_everyone()`.
        # So don't include it if it's value is the same as `AllowedMentions.not_everyone()`.
        allowed_mentions: Optional[AllowedMentions] = self.allowed_mentions
        if allowed_mentions == AllowedMentions.not_everyone():
            allowed_mentions = None

        # Create the Json
        return utils.dict_without_falsies(
            command_prefix=self.command_prefix,
            intents=(
                utils.dict_without_falsies(intents.to_json()) if intents else None
            ),
            privileged_intents=utils.dict_without_falsies(privileged_intents.to_json()),
            allowed_mentions=(
                utils.dict_without_falsies(allowed_mentions.to_json())
                if allowed_mentions
                else None
            ),
            extensions=[ext.to_json() for ext in self.extensions.values()],
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

    def get_extension(self, name: str) -> ConfiguredExtension:
        """
        Get an extension from the config.

        Parameters
        ----------
        name: :class:`str`
            The name of the extension to get.

        Raises
        ------
        ExtensionNotInConfig
            The extension was not in the config.
        """

        if ext := self.extensions.get(name):
            return ext
        raise ExtensionNotInConfig(name)

    def get_optional_extension(self, name: str) -> ConfiguredExtension:
        """
        Get an extension from the config that's not marked as required.

        Parameters
        ----------
        name: :class:`str`
            The name of the optional extension to get.

        Raises
        ------
        ExtensionNotInConfig
            The extension was not in the config.
        ExtensionIsRequired
            The extension was a required extension.
        """

        ext: ConfiguredExtension = self.get_extension(name)
        if not ext.required:
            return ext
        raise ExtensionIsRequired(name)

    def get_extension_options(self, name: str) -> Optional[JsonObject]:
        """
        Get the options for an extension.

        Parameters
        ----------
        name: :class:`str`
            The name of the extension to get options for.

        Raises
        ------
        ExtensionNotInConfig
            The extension was not in the config.
        """

        ext: ConfiguredExtension = self.get_extension(name)
        return ext.options

    def enable_extension(self, name: str):
        """
        Mark an extension as enabled in the config.

        Parameters
        ----------
        name: :class:`str`
            The name of the extension to enable.

        Raises
        ------
        ExtensionNotInConfig
            The extension was not in the config.
        """

        ext: ConfiguredExtension = self.get_extension(name)
        if ext in self.disabled_extensions:
            ext.disabled = False
            self._rebuild_extension_states()

    def disable_extension(self, name: str):
        """
        Mark an extension as disabled in the config.

        Parameters
        ----------
        name: :class:`str`
            The name of the extension to disable.

        Raises
        ------
        ExtensionNotInConfig
            The extension was not in the config.
        """

        ext: ConfiguredExtension = self.get_extension(name)
        if ext in self.enabled_extensions:
            ext.disabled = True
            self._rebuild_extension_states()
