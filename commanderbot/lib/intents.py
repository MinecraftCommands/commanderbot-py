import inspect
from typing import Any, Callable, ClassVar, Optional, Self, cast, override

import discord
from pydantic import GetCoreSchemaHandler, TypeAdapter
from pydantic_core import core_schema

from commanderbot.lib.exceptions import InstantiationError, NoSuchFactory
from commanderbot.lib.from_data_mixin import FromDataMixin
from commanderbot.lib.json_serializable import JsonSerializable

__all__ = ["Intents", "IntentsAdapter"]


class Intents(discord.Intents, FromDataMixin, JsonSerializable):
    """
    Extends `discord.Intents` to implement de/serialization and add extra features.

    Can be de/serialized using Pydantic or `FromDataMixin`/`JsonSerializeable`.
    """

    # @@ FACTORIES

    _factories: ClassVar[dict[str, Callable[[], Self]]] = {}

    # @overrides discord.Intents
    @override
    @classmethod
    def all(cls) -> Self:
        """
        A factory method that creates a :class:`Intents` with everything enabled.
        """
        return cast(Self, super().all())

    # @overrides discord.Intents
    @override
    @classmethod
    def none(cls) -> Self:
        """
        A factory method that creates a :class:`Intents` with everything disabled.
        """
        return cast(Self, super().none())

    # @overrides discord.Intents
    @override
    @classmethod
    def default(cls) -> Self:
        """
        A factory method that creates a :class:`Intents` with everything enabled
        except :attr:`presences`, :attr:`members`, and :attr:`message_content`.
        """
        return cast(Self, super().default())

    @classmethod
    def privileged(cls) -> Self:
        """
        A factory method that creates a :class:`Intents` with only :attr:`presences`,
        :attr:`members`, and :attr:`message_content` enabled.
        """
        return cls(message_content=True, members=True, presences=True)

    # @@ INSTANCE

    # @@ DE/SERIALIZATION

    # @implements FromDataMixin
    @override
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
    @override
    def to_json(self) -> Any:
        # A very hacky way to turn this instance into a `dict``.
        # Have no idea why `dict(self)` doesn't work.
        return dict(discord.Intents(self.value))

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

        def from_dict(raw_intents: dict[str, bool]) -> Self:
            try:
                return cls(**raw_intents)
            except Exception as ex:
                raise InstantiationError(cls, ex)

        def to_dict(instance: Self) -> dict:
            temp = discord.Intents(instance.value)
            return {k: v for k, v in temp if v}

        from_int_schema = core_schema.chain_schema(
            [
                core_schema.int_schema(),
                core_schema.no_info_plain_validator_function(
                    lambda v: cls._from_value(v)
                ),
            ]
        )

        from_factory_schema = core_schema.chain_schema(
            [
                core_schema.str_schema(),
                core_schema.no_info_plain_validator_function(from_factory),
            ]
        )

        from_dict_schema = core_schema.chain_schema(
            [
                core_schema.dict_schema(
                    keys_schema=core_schema.str_schema(),
                    values_schema=core_schema.bool_schema(),
                ),
                core_schema.no_info_plain_validator_function(from_dict),
            ]
        )

        return core_schema.json_or_python_schema(
            json_schema=core_schema.union_schema(
                [
                    from_factory_schema,
                    from_dict_schema,
                    from_int_schema,
                ]
            ),
            python_schema=core_schema.union_schema(
                [
                    core_schema.is_instance_schema(cls),
                    from_factory_schema,
                    from_dict_schema,
                    from_int_schema,
                ]
            ),
            serialization=core_schema.plain_serializer_function_ser_schema(to_dict),
        )


# Cache intents factories.
for name, func in inspect.getmembers(Intents, inspect.ismethod):
    # An intents factory takes no arguments and has a specific doc string.
    signature = inspect.signature(func)
    doc_str = inspect.getdoc(func) or ""
    if len(signature.parameters) == 0 and "A factory method that creates a" in doc_str:
        Intents._factories[name] = func

IntentsAdapter = TypeAdapter(Intents)
"""
A Pydantic type adapter that lets you de/serialize `Intents` outside of a Pydantic `BaseModel`.
"""
