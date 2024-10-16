from typing import Any, Self, cast

import discord
from discord.mentions import default

from commanderbot.lib.from_data_mixin import FromDataMixin
from commanderbot.lib.json_serializable import JsonSerializable

__all__ = ("AllowedMentions",)


class AllowedMentions(discord.AllowedMentions, JsonSerializable, FromDataMixin):
    """Extends `discord.AllowedMentions` to simplify de/serialization."""

    @classmethod
    def all(cls) -> Self:
        return cast(Self, super().all())

    @classmethod
    def none(cls) -> Self:
        return cast(Self, super().none())

    @classmethod
    def not_everyone(cls) -> Self:
        return cls(everyone=False, users=True, roles=True, replied_user=True)

    @classmethod
    def only_replies(cls) -> Self:
        return cls(everyone=False, users=False, roles=False, replied_user=True)

    @classmethod
    def only_users(cls) -> Self:
        return cls(everyone=False, users=True, roles=False, replied_user=False)

    @classmethod
    def only_roles(cls) -> Self:
        return cls(everyone=False, users=False, roles=True, replied_user=False)

    def merge(self, other: discord.AllowedMentions) -> Self:
        return cast(Self, super().merge(other))

    # @implements FromDataMixin
    @classmethod
    def try_from_data(cls, data):
        if isinstance(data, str):
            if factory := getattr(cls, data, None):
                return factory()
        if isinstance(data, dict):
            return cls(**data)

    # @implements JsonSerializable
    def to_json(self) -> Any:
        data = {}
        for field in self.__slots__:
            if (value := getattr(self, field, default)) is not default:
                data[field] = value
        return data

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, discord.AllowedMentions):
            return False

        for field in self.__slots__:
            self_value = getattr(self, field, default)
            other_value = getattr(other, field, default)
            if self_value != other_value:
                return False

        return True

    def __ne__(self, other: object) -> bool:
        return not self.__eq__(other)
