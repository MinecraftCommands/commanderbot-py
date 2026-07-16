import inspect
from typing import Any, Callable, ClassVar, Optional, Self, cast, override

import discord
from pydantic import GetCoreSchemaHandler, TypeAdapter
from pydantic_core import core_schema

from commanderbot.lib.exceptions import InstantiationError, NoSuchFactory
from commanderbot.lib.from_data_mixin import FromDataMixin
from commanderbot.lib.json_serializable import JsonSerializable

__all__ = ["Color", "ColorAdapter"]


class Color(discord.Colour, FromDataMixin, JsonSerializable):
    """
    Extends `discord.Color` to implement de/serialization and add extra features.

    Can be de/serialized using Pydantic or `FromDataMixin`/`JsonSerializeable`.
    """

    # @@ FACTORIES

    _factories: ClassVar[dict[str, Callable[[], Self]]] = {}

    # @overrides discord.Colour
    @override
    @classmethod
    def from_str(cls, value: str) -> Self:
        # The classmethod, `discord.Color.from_str()`, always returns a
        # `discord.Color` regardless of what `cls` is. So we cast it
        # to this class.
        return cast(Self, super().from_str(value))

    @classmethod
    def presets(
        cls, *, color_filter: Optional[str] = None, case_sensitive: bool = False
    ) -> dict[str, "Color"]:
        """
        Returns a dictionary containing all color presets.
        The `color_filter` parameter can be used to filter the color presets that are returned.
        """

        color_filter = color_filter and (
            color_filter if case_sensitive else color_filter.lower()
        )
        colors: dict[str, Color] = {}
        for name, func in cls._factories.items():
            # Skip factory function if its name doesn't contain the color filter.
            func_name: str = name if case_sensitive else name.lower()
            if color_filter and color_filter not in func_name:
                continue

            colors[name] = func()

        return colors

    @classmethod
    def white(cls) -> Self:
        """A factory method that returns a :class:`Color` with a value of ``0xFFFFFF``.

        .. color:: #FFFFFF
        """
        return cls(0xFFFFFF)

    @classmethod
    def mcc_blue(cls) -> Self:
        """A factory method that returns a :class:`Color` with a value of ``0x00ACED``.

        .. color:: #00ACED
        """
        return cls(0x00ACED)

    @classmethod
    def mojang_red(cls) -> Self:
        """A factory method that returns a :class:`Color` with a value of ``0xF0313B``.

        .. color:: #F0313B
        """
        return cls(0xF0313B)

    @classmethod
    def minecoin_gold(cls) -> Self:
        """A factory method that returns a :class:`Color` with a value of ``0xDDD605``.

        .. color:: #DDD605
        """
        return cls(0xDDD605)

    @classmethod
    def minecraft_black(cls) -> Self:
        """A factory method that returns a :class:`Color` with a value of ``0x000000``.

        .. color:: #000000
        """
        return cls(0x000000)

    @classmethod
    def minecraft_dark_blue(cls) -> Self:
        """A factory method that returns a :class:`Color` with a value of ``0x0000AA``.

        .. color:: #0000AA
        """
        return cls(0x0000AA)

    @classmethod
    def minecraft_dark_green(cls) -> Self:
        """A factory method that returns a :class:`Color` with a value of ``0x00AA00``.

        .. color:: #00AA00
        """
        return cls(0x00AA00)

    @classmethod
    def minecraft_dark_aqua(cls) -> Self:
        """A factory method that returns a :class:`Color` with a value of ``0x00AAAA``.

        .. color:: #00AAAA
        """
        return cls(0x00AAAA)

    @classmethod
    def minecraft_dark_red(cls) -> Self:
        """A factory method that returns a :class:`Color` with a value of ``0xAA0000``.

        .. color:: #AA0000
        """
        return cls(0xAA0000)

    @classmethod
    def minecraft_dark_purple(cls) -> Self:
        """A factory method that returns a :class:`Color` with a value of ``0xAA00AA``.

        .. color:: #AA00AA
        """
        return cls(0xAA00AA)

    @classmethod
    def minecraft_gold(cls) -> Self:
        """A factory method that returns a :class:`Color` with a value of ``0xFFAA00``.

        .. color:: #FFAA00
        """
        return cls(0xFFAA00)

    @classmethod
    def minecraft_gray(cls) -> Self:
        """A factory method that returns a :class:`Color` with a value of ``0xAAAAAA``.

        .. color:: #AAAAAA
        """
        return cls(0xAAAAAA)

    @classmethod
    def minecraft_dark_gray(cls) -> Self:
        """A factory method that returns a :class:`Color` with a value of ``0x555555``.

        .. color:: #555555
        """
        return cls(0x555555)

    @classmethod
    def minecraft_blue(cls) -> Self:
        """A factory method that returns a :class:`Color` with a value of ``0x5555FF``.

        .. color:: #5555FF
        """
        return cls(0x5555FF)

    @classmethod
    def minecraft_green(cls) -> Self:
        """A factory method that returns a :class:`Color` with a value of ``0x55FF55``.

        .. color:: #55FF55
        """
        return cls(0x55FF55)

    @classmethod
    def minecraft_aqua(cls) -> Self:
        """A factory method that returns a :class:`Color` with a value of ``0x55FFFF``.

        .. color:: #55FFFF
        """
        return cls(0x55FFFF)

    @classmethod
    def minecraft_red(cls) -> Self:
        """A factory method that returns a :class:`Color` with a value of ``0xFF5555``.

        .. color:: #FF5555
        """
        return cls(0xFF5555)

    @classmethod
    def minecraft_light_purple(cls) -> Self:
        """A factory method that returns a :class:`Color` with a value of ``0xFF55FF``.

        .. color:: #FF55FF
        """
        return cls(0xFF55FF)

    @classmethod
    def minecraft_yellow(cls) -> Self:
        """A factory method that returns a :class:`Color` with a value of ``0xFFFF55``.

        .. color:: #FFFF55
        """
        return cls(0xFFFF55)

    @classmethod
    def minecraft_white(cls) -> Self:
        """A factory method that returns a :class:`Color` with a value of ``0xFFFFFF``.

        .. color:: #FFFFFF
        """
        return cls(0xFFFFFF)

    @classmethod
    def minecraft_material_quartz(cls) -> Self:
        """A factory method that returns a :class:`Color` with a value of ``0xE3D4D1``.

        .. color:: #E3D4D1
        """
        return cls(0xE3D4D1)

    @classmethod
    def minecraft_material_iron(cls) -> Self:
        """A factory method that returns a :class:`Color` with a value of ``0xCECACA``.

        .. color:: #CECACA
        """
        return cls(0xCECACA)

    @classmethod
    def minecraft_material_netherite(cls) -> Self:
        """A factory method that returns a :class:`Color` with a value of ``0x443A3B``.

        .. color:: #443A3B
        """
        return cls(0x443A3B)

    @classmethod
    def minecraft_material_redstone(cls) -> Self:
        """A factory method that returns a :class:`Color` with a value of ``0x971607``.

        .. color:: #971607
        """
        return cls(0x971607)

    @classmethod
    def minecraft_material_copper(cls) -> Self:
        """A factory method that returns a :class:`Color` with a value of ``0xB4684D``.

        .. color:: #B4684D
        """
        return cls(0xB4684D)

    @classmethod
    def minecraft_material_gold(cls) -> Self:
        """A factory method that returns a :class:`Color` with a value of ``0xDEB12D``.

        .. color:: #DEB12D
        """
        return cls(0xDEB12D)

    @classmethod
    def minecraft_material_emerald(cls) -> Self:
        """A factory method that returns a :class:`Color` with a value of ``0x47A036``.

        .. color:: #47A036
        """
        return cls(0x47A036)

    @classmethod
    def minecraft_material_diamond(cls) -> Self:
        """A factory method that returns a :class:`Color` with a value of ``0x2CBAA8``.

        .. color:: #2CBAA8
        """
        return cls(0x2CBAA8)

    @classmethod
    def minecraft_material_lapis(cls) -> Self:
        """A factory method that returns a :class:`Color` with a value of ``0x21497B``.

        .. color:: #21497B
        """
        return cls(0x21497B)

    @classmethod
    def minecraft_material_amethyst(cls) -> Self:
        """A factory method that returns a :class:`Color` with a value of ``0x9A5CC6``.

        .. color:: #9A5CC6
        """
        return cls(0x9A5CC6)

    @classmethod
    def minecraft_material_resin(cls) -> Self:
        """A factory method that returns a :class:`Color` with a value of ``0xEB7114``.

        .. color:: #EB7114
        """
        return cls(0xEB7114)

    # @@ INSTANCE

    def to_hex(self) -> str:
        return str(self)

    # @overrides discord.Colour
    @override
    def __repr__(self) -> str:
        return f"0x{self.value:X}"

    # @@ DE/SERIALIZATION

    # @implements FromDataMixin
    @override
    @classmethod
    def try_from_data(cls, data) -> Optional[Self]:
        if isinstance(data, str):
            return cls.from_str(data)
        elif isinstance(data, int):
            return cls(data)
        elif isinstance(data, dict):
            return cls.from_field_optional(data, "color")

    # @implements JsonSerializable
    @override
    def to_json(self) -> Any:
        return str(self)

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

        from_int_schema = core_schema.chain_schema(
            [
                core_schema.int_schema(),
                core_schema.no_info_plain_validator_function(lambda v: cls(v)),
            ]
        )

        from_str_schema = core_schema.chain_schema(
            [
                core_schema.str_schema(),
                core_schema.no_info_plain_validator_function(lambda v: cls.from_str(v)),
            ]
        )

        from_factory_schema = core_schema.chain_schema(
            [
                core_schema.literal_schema([*cls._factories]),
                core_schema.no_info_plain_validator_function(from_factory),
            ]
        )

        from_rgb_dict_schema = core_schema.chain_schema(
            [
                core_schema.dict_schema(
                    keys_schema=core_schema.literal_schema(["r", "g", "b"]),
                    values_schema=core_schema.int_schema(),
                    min_length=3,
                    max_length=3,
                ),
                core_schema.no_info_plain_validator_function(
                    lambda d: cls.from_rgb(**d)
                ),
            ]
        )

        from_hsv_dict_schema = core_schema.chain_schema(
            [
                core_schema.dict_schema(
                    keys_schema=core_schema.literal_schema(["h", "s", "v"]),
                    values_schema=core_schema.union_schema(
                        [core_schema.float_schema(), core_schema.int_schema()]
                    ),
                    min_length=3,
                    max_length=3,
                ),
                core_schema.no_info_plain_validator_function(
                    lambda d: cls.from_hsv(**d)
                ),
            ]
        )

        return core_schema.json_or_python_schema(
            json_schema=core_schema.union_schema(
                [
                    from_factory_schema,
                    from_rgb_dict_schema,
                    from_hsv_dict_schema,
                    from_str_schema,
                    from_int_schema,
                ]
            ),
            python_schema=core_schema.union_schema(
                [
                    core_schema.is_instance_schema(cls),
                    from_factory_schema,
                    from_rgb_dict_schema,
                    from_hsv_dict_schema,
                    from_str_schema,
                    from_int_schema,
                ]
            ),
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda c: str(c)
            ),
        )


# Cache color factories.
for name, func in inspect.getmembers(Color, inspect.ismethod):
    # A color factory takes no arguments and has a specific doc string.
    signature = inspect.signature(func)
    doc_str = inspect.getdoc(func) or ""
    if len(signature.parameters) == 0 and "value of ``0x" in doc_str:
        Color._factories[name] = func

ColorAdapter = TypeAdapter(Color)
"""
A Pydantic type adapter that lets you de/serialize `Color` outside of a Pydantic `BaseModel`.
"""
