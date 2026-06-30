from logging import Logger, getLogger
from typing import Any, Optional, Self, override

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    PrivateAttr,
    SerializerFunctionWrapHandler,
    model_serializer,
    model_validator,
)

from commanderbot.core.exceptions import ExtensionIsRequired, ExtensionNotInConfig
from commanderbot.lib import (
    AllowedMentions,
    AllowedMentionsAdapter,
    Intents,
    JsonObject,
)


class ConfiguredExtension(BaseModel):
    """
    Represents an extension with an optional config.

    Attributes
    ----------
    name: :class:`str`
        The name of this extension (Should be the same as its import path).
    required: :class:`bool`
        Whether this extension is required or not. It doesn't affect loading/unloading/reloading this extension,
        but you're free to choose how to handle this attribute in your code. Defaults to `False`.
    disabled: :class:`bool`
        Whether this extension is disabled or not. Defaults to `False`.
    options: :class:`Optional[JsonObject]`
        Options for this extension. Defaults to `None`.
    """

    name: str
    required: bool = False
    disabled: bool = False
    options: Optional[JsonObject] = None

    @model_validator(mode="before")
    @classmethod
    def _validate_model(cls, data: Any) -> Any:
        if isinstance(data, str):
            # Extensions starting with a `$` are required.
            if data.startswith("$"):
                return {"name": data[1:], "required": True}
            # Extensions starting with a `!` are disabled.
            elif data.startswith("!"):
                return {"name": data[1:], "disabled": True}
            else:
                return {"name": data}
        else:
            return data

    @model_serializer(mode="wrap")
    def _serialize_model(self, handler: SerializerFunctionWrapHandler) -> dict | str:
        if self.options:
            return handler(self)
        elif self.required:
            return f"${self.name}"
        elif self.disabled:
            return f"!{self.name}"
        else:
            return self.name


class Config(BaseModel):
    """
    Attributes
    ----------
    command_prefix :class:`str`
        The prefix to use for prefix commands.
    gateway_intents :class:`Intents`
        Non-privileged intents to use. Defaults to `Intents.default()`.
    privileged_gateway_intents :class:`Intents`
        Privileged intents to use. Defaults to `Intents.none()`.
    allowed_mentions :class:`AllowedMentions`
        The allowed mentions to use. Defaults to `AllowedMentions.not_everyone()`.
    extensions :class:`list[ConfiguredExtension]`
        The list of extensions to use.
    """

    model_config = ConfigDict(serialize_by_alias=True)

    command_prefix: str
    gateway_intents: Intents = Field(alias="intents", default_factory=Intents.default)
    privileged_gateway_intents: Intents = Field(
        alias="privileged_intents", default_factory=Intents.none
    )
    allowed_mentions: AllowedMentions = Field(
        default_factory=AllowedMentions.not_everyone
    )
    extensions: list[ConfiguredExtension] = Field(default_factory=list)

    _extensions_by_name: dict[str, ConfiguredExtension] = PrivateAttr(
        default_factory=dict
    )
    _enabled_extensions: list[ConfiguredExtension] = PrivateAttr(default_factory=list)
    _disabled_extensions: list[ConfiguredExtension] = PrivateAttr(default_factory=list)

    @property
    def intents(self) -> Intents:
        """
        The intents that result from merging `gateway_intents` and `privileged_gateway_intents`.
        """
        return self.gateway_intents | self.privileged_gateway_intents

    @property
    def extensions_by_name(self) -> dict[str, ConfiguredExtension]:
        """
        A dictionary of extensions where the key is the name and the value is a `ConfiguredExtension`.
        """
        return self._extensions_by_name

    @property
    def enabled_extensions(self) -> list[ConfiguredExtension]:
        """
        A list of enabled extensions.
        """
        return self._enabled_extensions

    @property
    def disabled_extensions(self) -> list[ConfiguredExtension]:
        """
        A list of disabled extensions.
        """
        return self._disabled_extensions

    @model_validator(mode="after")
    def _validate_model(self) -> Self:
        self.gateway_intents &= Intents.default()
        self.privileged_gateway_intents &= Intents.privileged()
        return self

    @model_serializer(mode="wrap")
    def _serialize_model(self, handler: SerializerFunctionWrapHandler) -> dict:
        self.gateway_intents &= Intents.default()
        self.privileged_gateway_intents &= Intents.privileged()

        # Serialize model and remove keys with falsy values
        result: dict = handler(self)
        return {k: v for k, v in result.items() if v}

    # @overrides BaseModel
    @override
    def model_post_init(self, context: Any):
        self._extensions_by_name.clear()
        self._enabled_extensions.clear()
        self._disabled_extensions.clear()
        for ext in self.extensions:
            self._extensions_by_name[ext.name] = ext
            if ext.disabled:
                self.disabled_extensions.append(ext)
            else:
                self.enabled_extensions.append(ext)

    def _rebuild_extension_states(self):
        self._enabled_extensions.clear()
        self._disabled_extensions.clear()
        for ext in self.extensions:
            if ext.disabled:
                self.disabled_extensions.append(ext)
            else:
                self.enabled_extensions.append(ext)

    def log_info(self):
        log: Logger = getLogger(__name__)
        log.info(f"Command prefix: {self.command_prefix}")
        log.info(f"Using intents flags: {self.intents.value}")
        log.info(
            f"Using allowed mentions: {AllowedMentionsAdapter.dump_python(self.allowed_mentions)}"
        )

        if self.extensions:
            log.info(
                f"Processed {len(self.extensions)} extensions (Enabled: {len(self._enabled_extensions)} | Disabled: {len(self._disabled_extensions)})"
            )
        else:
            log.warning("No extensions configured.")

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

        if ext := self._extensions_by_name.get(name):
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
        if ext in self._disabled_extensions:
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
        if ext in self._enabled_extensions:
            ext.disabled = True
            self._rebuild_extension_states()
