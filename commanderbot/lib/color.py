import inspect
from typing import Optional, Self

import discord

from commanderbot.lib.from_data_mixin import FromDataMixin

__all__ = ("Color",)


class Color(discord.Color, FromDataMixin):
    """Extends `discord.Color` to simplify deserialization."""

    # @overrides discord.Color
    def __repr__(self) -> str:
        return f"0x{self.value:X}"

    # @overrides discord.Color
    @classmethod
    def from_str(cls, value: str) -> Self:
        # The classmethod, `discord.Color.from_str()`, always returns a
        # `discord.Color` regardless of what `cls` is. So we need to
        # construct our `cls` using a temporary `discord.Color`.
        temp: discord.Color = super().from_str(value)
        return cls(temp.value)

    # @overrides FromDataMixin
    @classmethod
    def try_from_data(cls, data):
        if isinstance(data, str):
            return cls.from_str(data)
        elif isinstance(data, int):
            return cls(data)
        elif isinstance(data, dict):
            return cls.from_field_optional(data, "color")

    @classmethod
    def presets(
        cls, *, color_filter: Optional[str] = None, case_sensitive: bool = False
    ) -> dict[str, "Color"]:
        """
        Returns a dictionary containing all color presets.
        The `color_filter` parameter can be used to filter the color presets that are returned
        """

        color_filter = color_filter and (
            color_filter if case_sensitive else color_filter.lower()
        )
        colors: dict[str, Color] = {}
        for name, func in inspect.getmembers(Color, inspect.ismethod):
            # If we're seaching for specific functions, skip the current
            # function if it doesn't have the string we're searching for.
            func_name: str = name if case_sensitive else name.lower()
            if color_filter and color_filter not in func_name:
                continue

            # Check if the current function is one of the `@classmethod`s that
            # take no arguments and return this class/`discord.Color``
            signature = inspect.signature(func)
            doc_str = inspect.getdoc(func) or ""
            if len(signature.parameters) == 0 and "value of ``0" in doc_str:
                colors[name] = func()

        return colors

    def to_hex(self) -> str:
        return str(self)

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
    def minecraft_green(cls) -> Self:
        """A factory method that returns a :class:`Color` with a value of ``0x00AA00``.

        .. color:: #00AA00
        """
        return cls(0x00AA00)

    @classmethod
    def minecraft_gold(cls) -> Self:
        """A factory method that returns a :class:`Color` with a value of ``0xFFAA00``.

        .. color:: #FFAA00
        """
        return cls(0xFFAA00)

    @classmethod
    def minecraft_material_emerald(cls) -> Self:
        """A factory method that returns a :class:`Color` with a value of ``0x47A036``.

        .. color:: #47A036
        """
        return cls(0x47A036)

    @classmethod
    def minecraft_material_gold(cls) -> Self:
        """A factory method that returns a :class:`Color` with a value of ``0xDEB12D``.

        .. color:: #DEB12D
        """
        return cls(0xDEB12D)
