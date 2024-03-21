from typing import Any, Dict, TypeAlias

from discord import (
    DMChannel,
    GroupChannel,
    Guild,
    Member,
    Message,
    PartialMessageable,
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
    "RoleID",
    "UserID",
    "ForumTagID",
    "AppCommandID",
    "RawOptions",
    "JsonObject",
    "MemberOrUser",
    "PartialMessageableChannel",
    "MessageableChannel",
    "UnmentionableMessageableChannel",
    "MessageableGuildChannel",
    "TextMessage",
    "TextReaction",
    "GuildContext",
    "MemberContext",
)


IDType: TypeAlias = int

GuildID: TypeAlias = IDType
ChannelID: TypeAlias = IDType
RoleID: TypeAlias = IDType
UserID: TypeAlias = IDType
ForumTagID: TypeAlias = IDType
AppCommandID: TypeAlias = IDType

RawOptions: TypeAlias = Any

JsonObject: TypeAlias = Dict[str, Any]

MemberOrUser: TypeAlias = Member | User

PartialMessageableChannel: TypeAlias = (
    TextChannel | VoiceChannel | StageChannel | Thread | DMChannel | PartialMessageable
)
"""
Channel types that can be partial messageable.

A redefinition of the type alias found in `discord.abc`.
"""

MessageableChannel: TypeAlias = PartialMessageableChannel | GroupChannel
"""
Channel types that messages can be sent in.

A redefinition of the type alias found in `discord.abc`.
"""

UnmentionableMessageableChannel: TypeAlias = (
    DMChannel | GroupChannel | PartialMessageable
)
"""
Channel types that messages can be sent in, but have no way to be mentioned.
"""

MessageableGuildChannel: TypeAlias = TextChannel | Thread | VoiceChannel | StageChannel
"""
Channel types that are messageable in a guild
"""


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


class GuildContext(Context):
    """
    A [Context] from within a [Guild].

    This is a dummy class that can be used in casts to convince static analysis that
    this [Context] does indeed contain a [Guild].

    This is not intended to be used anywhere other than type-hinting.
    """

    guild: Guild


class MemberContext(GuildContext):
    """
    A [Context] from within a [Guild] with an author that is a [Member].

    This is a dummy class that can be used in casts to convince static analysis that
    this [Context] contains an `author` that is a [Member] and not just a [User].

    This is not intended to be used anywhere other than type-hinting.
    """

    author: Member
