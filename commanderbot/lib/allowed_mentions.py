import inspect
from collections.abc import Callable
from typing import Any, ClassVar, Optional, Self, cast, override

import discord
from discord.mentions import default
from pydantic import GetCoreSchemaHandler, TypeAdapter
from pydantic_core import core_schema

from commanderbot.lib.exceptions import InstantiationError, NoSuchFactory
from commanderbot.lib.from_data_mixin import FromDataMixin
from commanderbot.lib.json_serializable import JsonSerializable

__all__ = ["AllowedMentions", "AllowedMentionsAdapter"]


class AllowedMentions(discord.AllowedMentions, FromDataMixin, JsonSerializable):
    """
    Extends `discord.AllowedMentions` to implement de/serialization and add extra features.

    Can be de/serialized using Pydantic or `FromDataMixin`/`JsonSerializeable`.
    """

    # @@ FACTORIES

    _factories: ClassVar[dict[str, Callable[[], Self]]] = {}

    @classmethod
    def not_everyone(cls) -> Self:
        """
        A factory method that returns a :class:`AllowedMentions` with all fields except ``everyone`` set to ``True``
        """
        return cls(everyone=False, users=True, roles=True, replied_user=True)

    @classmethod
    def only_replies(cls) -> Self:
        """
        A factory method that returns a :class:`AllowedMentions` with only the ``replied_user`` field set to ``True``
        """
        return cls(everyone=False, users=False, roles=False, replied_user=True)

    @classmethod
    def only_users(cls) -> Self:
        """
        A factory method that returns a :class:`AllowedMentions` with only the ``users`` field set to ``True``
        """
        return cls(everyone=False, users=True, roles=False, replied_user=False)

    @classmethod
    def only_roles(cls) -> Self:
        """
        A factory method that returns a :class:`AllowedMentions` with only the ``roles`` field set to ``True``
        """
        return cls(everyone=False, users=False, roles=True, replied_user=False)

    # @@ INSTANCE

    @override
    def merge(self, other: discord.AllowedMentions) -> Self:
        return cast(Self, super().merge(other))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, discord.AllowedMentions):
            return False

        for field in self.__slots__:
            self_value = getattr(self, field, default)
            other_value = getattr(self, field, default)
            if self_value != other_value:
                return False

        return True

    def __ne__(self, other: object) -> bool:
        return not self.__eq__(other)

    # @@ DE/SERIALIZATION

    # @implements FromDataMixin
    @override
    @classmethod
    def try_from_data(cls, data) -> Optional[Self]:
        if isinstance(data, str):
            if factory := getattr(cls, data, None):
                return factory()
        if isinstance(data, dict):
            return cls(**data)

    # @implements JsonSerializable
    @override
    def to_json(self) -> Any:
        data = {}
        for field in self.__slots__:
            if (value := getattr(self, field, default)) is not default:
                data[field] = value
        return data

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        def from_factory(factory_name: str) -> Self:
            if factory := cls._factories.get(factory_name):
                try:
                    return factory()
                except Exception as ex:
                    raise InstantiationError(cls, ex)
            raise NoSuchFactory(cls, factory_name)

        def from_dict(raw_allowed_mentions: dict[str, bool]):
            try:
                return cls(**raw_allowed_mentions)
            except Exception as ex:
                raise InstantiationError(cls, ex)

        def to_dict(instance: Self) -> dict:
            data = {}
            for field in cls.__slots__:
                if (value := getattr(instance, field, default)) is not default:
                    data[field] = value

            return data

        from_factory_schema = core_schema.chain_schema(
            [
                core_schema.literal_schema([*cls._factories]),
                core_schema.no_info_plain_validator_function(from_factory),
            ]
        )

        from_dict_schema = core_schema.chain_schema(
            [
                core_schema.dict_schema(
                    keys_schema=core_schema.literal_schema([*cls.__slots__]),
                    values_schema=core_schema.bool_schema(),
                ),
                core_schema.no_info_plain_validator_function(from_dict),
            ]
        )

        return core_schema.json_or_python_schema(
            json_schema=core_schema.union_schema(
                [from_factory_schema, from_dict_schema]
            ),
            python_schema=core_schema.union_schema(
                [
                    core_schema.is_instance_schema(cls),
                    from_factory_schema,
                    from_dict_schema,
                ]
            ),
            serialization=core_schema.plain_serializer_function_ser_schema(to_dict),
        )


# Cache allowed mentions factories.
for name, func in inspect.getmembers(AllowedMentions, inspect.ismethod):
    # An allowed mentions factory takes no arguments and has a specific doc string.
    signature = inspect.signature(func)
    doc_str = inspect.getdoc(func) or ""
    if len(signature.parameters) == 0 and "A factory method that returns a" in doc_str:
        AllowedMentions._factories[name] = func


AllowedMentionsAdapter = TypeAdapter(AllowedMentions)
"""
A Pydantic type adapter that lets you de/serialize `AllowedMentions` outside of a Pydantic `BaseModel`.
"""
