from typing import Annotated, Any

import discord
from pydantic import PlainSerializer, PlainValidator

from commanderbot.lib.types import ChannelTypeNames

__all__ = ("ChannelType",)


def _validate_channel_type(data: Any) -> discord.ChannelType:
    if isinstance(data, discord.ChannelType):
        return data

    try:
        return discord.ChannelType[data]
    except KeyError as ex:
        raise ValueError(f"'{data}' is not a valid 'ChannelType'") from ex


ChannelType = Annotated[
    discord.ChannelType,
    PlainValidator(_validate_channel_type, json_schema_input_type=ChannelTypeNames),
    PlainSerializer(lambda value: value.name, return_type=ChannelTypeNames),
]
"""
This is the `discord.ChannelType` enum, but with Pydantic support.
"""
