from discord import (
    CategoryChannel,
    DMChannel,
    ForumChannel,
    GroupChannel,
    Guild,
    Member,
    PartialMessageable,
    StageChannel,
    TextChannel,
    Thread,
    User,
    VoiceChannel,
)
from typing_extensions import TypeIs

from commanderbot.lib.types import (
    ConnectableChannel,
    MessageableChannel,
    MessageableGuildChannel,
)

__all__ = (
    "is_user",
    "is_member",
    "is_guild",
    "is_text_channel",
    "is_forum_channel",
    "is_thread",
    "is_voice_channel",
    "is_stage_channel",
    "is_dm_channel",
    "is_group_dm_channel",
    "is_category_channel",
    "is_messagable_channel",
    "is_messagable_guild_channel",
    "is_connectable_channel",
    "is_partial_messagable",
)


def is_user(obj: object) -> TypeIs[User]:
    return isinstance(obj, User)


def is_member(obj: object) -> TypeIs[Member]:
    return isinstance(obj, Member)


def is_guild(obj: object) -> TypeIs[Guild]:
    return isinstance(obj, Guild)


def is_text_channel(obj: object) -> TypeIs[TextChannel]:
    return isinstance(obj, TextChannel)


def is_forum_channel(obj: object) -> TypeIs[ForumChannel]:
    return isinstance(obj, ForumChannel)


def is_thread(obj: object) -> TypeIs[Thread]:
    return isinstance(obj, Thread)


def is_voice_channel(obj: object) -> TypeIs[VoiceChannel]:
    return isinstance(obj, VoiceChannel)


def is_stage_channel(obj: object) -> TypeIs[StageChannel]:
    return isinstance(obj, StageChannel)


def is_dm_channel(obj: object) -> TypeIs[DMChannel]:
    return isinstance(obj, DMChannel)


def is_group_dm_channel(obj: object) -> TypeIs[GroupChannel]:
    return isinstance(obj, GroupChannel)


def is_category_channel(obj: object) -> TypeIs[CategoryChannel]:
    return isinstance(obj, CategoryChannel)


def is_messagable_channel(obj: object) -> TypeIs[MessageableChannel]:
    return (
        is_text_channel(obj)
        or is_thread(obj)
        or is_voice_channel(obj)
        or is_stage_channel(obj)
        or is_dm_channel(obj)
        or is_group_dm_channel(obj)
    )


def is_messagable_guild_channel(obj: object) -> TypeIs[MessageableGuildChannel]:
    return (
        is_text_channel(obj)
        or is_thread(obj)
        or is_voice_channel(obj)
        or is_stage_channel(obj)
    )


def is_connectable_channel(obj: object) -> TypeIs[ConnectableChannel]:
    return is_voice_channel(obj) or is_stage_channel(obj)


def is_partial_messagable(obj: object) -> TypeIs[PartialMessageable]:
    return isinstance(obj, PartialMessageable)
