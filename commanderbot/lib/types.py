from typing import Any, TypeAlias

from discord import (
    CategoryChannel,
    DMChannel,
    ForumChannel,
    GroupChannel,
    Guild,
    Member,
    Message,
    Reaction,
    StageChannel,
    TextChannel,
    Thread,
    User,
    VoiceChannel,
)
from discord.ext.commands import Context, MessageConverter

__all__ = (
    "IDType",
    "GuildID",
    "ChannelID",
    "MessageID",
    "RoleID",
    "UserID",
    "ForumTagID",
    "AppCommandID",
    "EmojiID",
    "RawOptions",
    "JsonObject",
    "MemberOrUser",
    "Channel",
    "GuildChannel",
    "MessageableChannel",
    "MessageableGuildChannel",
    "ConnectableChannel",
    "TextMessage",
    "TextReaction",
)


IDType: TypeAlias = int

GuildID: TypeAlias = IDType
ChannelID: TypeAlias = IDType
MessageID: TypeAlias = IDType
RoleID: TypeAlias = IDType
UserID: TypeAlias = IDType
ForumTagID: TypeAlias = IDType
AppCommandID: TypeAlias = IDType
EmojiID: TypeAlias = IDType

RawOptions: TypeAlias = Any

JsonObject: TypeAlias = dict[str, Any]

MemberOrUser: TypeAlias = Member | User

Channel: TypeAlias = (
    TextChannel
    | ForumChannel
    | Thread
    | VoiceChannel
    | StageChannel
    | DMChannel
    | GroupChannel
    | CategoryChannel
)
GuildChannel: TypeAlias = (
    TextChannel | ForumChannel | Thread | VoiceChannel | StageChannel | CategoryChannel
)
MessageableChannel: TypeAlias = (
    TextChannel | Thread | VoiceChannel | StageChannel | DMChannel | GroupChannel
)
MessageableGuildChannel: TypeAlias = TextChannel | Thread | VoiceChannel | StageChannel
ConnectableChannel: TypeAlias = VoiceChannel | StageChannel


class TextMessage(Message):
    """
    A [Message] in a [TextChannel] or [Thread].

    This is a dummy class that can be used in casts to convince static analysis that
    this [Message] does indeed contain a [TextChannel] and [Guild].

    This is not intended to be used anywhere other than type-hinting.
    """

    channel: TextChannel | Thread
    guild: Guild

    @classmethod
    async def convert(cls, ctx: Context, argument: Any):
        """
        Attempt to convert the given argument into a `Role` from within a `Guild`.

        Note that discord.py's built-in `Role` is special-cased, so what we do here is
        explicitly make this subclass convertible and then just return the underlying
        `Role` anyway.
        """
        return await MessageConverter().convert(ctx, argument)


class TextReaction(Reaction):
    """
    A [Reaction] to a [Message] in a [TextChannel].

    This is a dummy class that can be used in casts to convince static analysis that
    this [Reaction] does indeed contain a [TextMessage].

    This is not intended to be used anywhere other than type-hinting.
    """

    message: TextMessage
