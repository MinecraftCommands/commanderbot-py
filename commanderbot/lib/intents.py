from typing import Any, Optional, Self, cast

import discord

from commanderbot.lib.from_data_mixin import FromDataMixin
from commanderbot.lib.json_serializable import JsonSerializable

__all__ = ("Intents",)


class Intents(discord.Intents, JsonSerializable, FromDataMixin):
    """Extends `discord.Intents` to simplify de/serialization."""

    @classmethod
    def all(cls) -> Self:
        return cast(Self, super().all())

    @classmethod
    def none(cls) -> Self:
        return cast(Self, super().none())

    @classmethod
    def default(cls) -> Self:
        return cast(Self, super().default())

    @classmethod
    def privileged(cls) -> Self:
        """A factory method that creates a :class:`Intents` with only :attr:`presences`,
        :attr:`members`, and :attr:`message_content` enabled.
        """
        return cls(message_content=True, members=True, presences=True)

    # @implements FromDataMixin
    @classmethod
    def try_from_data(cls, data) -> Optional[Self]:
        if isinstance(data, int):
            return cls._from_value(data)
        elif isinstance(data, str):
            if intents_factory := getattr(cls, data, None):
                return intents_factory()
        elif isinstance(data, dict):
            return cls(**data)

    # @implements JsonSerializable
    def to_json(self) -> Any:
        # A very hacky way to turn this instance into a `dict``.
        # Have no idea why `dict(self)` doesn't work.
        return dict(discord.Intents(self.value))
