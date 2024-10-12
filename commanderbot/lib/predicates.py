import re
from typing import Any, Optional, TypeIs

from discord import (
    AppInfo,
    CategoryChannel,
    Client,
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
from discord.ext.commands import Bot

from commanderbot.lib.types import (
    ConnectableChannel,
    MessageableChannel,
    MessageableGuildChannel,
    UserID,
)

__all__ = (
    "is_bot",
    "is_owner",
    "is_convertable_to",
    "is_invite_link",
    "is_message_link",
    "is_custom_emoji",
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

INVITE_LINK_PATTERN = re.compile(
    r"(?:https?://)?discord(?:app)?\.(?:com/invite|gg)/[a-zA-Z0-9]+/?"
)
MESSAGE_LINK_PATTERN = re.compile(
    r"https?://(?:\w*\.)?discord(?:app)?\.com/channels/(\d+|@me)/(\d+)/(\d+)"
)
CUSTOM_EMOJI_PATTERN = re.compile(r"\<a?\:\w+\:\d+\>")


def is_bot(bot: Bot, user: User | Member | UserID) -> bool:
    if not bot.user:
        return False
    elif is_user(user) or is_member(user):
        return user == bot.user
    else:
        return user == bot.user.id


def is_owner(client: Client, user: User | Member) -> bool:
    info: Optional[AppInfo] = client.application
    if not info:
        return False

    if info.team:
        return user in info.team.members
    else:
        return user == info.owner


def is_invite_link(invite: str) -> bool:
    """Return true if `invite` is a valid Discord invite link"""
    return bool(INVITE_LINK_PATTERN.match(invite))


def is_message_link(message: str) -> bool:
    """Return true if `message` is a valid Discord message link"""
    return bool(MESSAGE_LINK_PATTERN.match(message))


def is_custom_emoji(emoji: str) -> bool:
    """Return true if `emoji` is a valid custom Discord emoji"""
    return bool(CUSTOM_EMOJI_PATTERN.match(emoji))


def is_convertable_to(obj: Any, ty: Any) -> bool:
    try:
        ty(obj)
        return True
    except:
        return False


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
