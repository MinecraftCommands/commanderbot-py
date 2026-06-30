from typing import Any, Literal, TypeAlias

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
    "CategoryID",
    "ChannelID",
    "ThreadID",
    "MessageID",
    "RoleID",
    "UserID",
    "ForumTagID",
    "AppCommandID",
    "EmojiID",
    "DiscordAutomodRuleID",
    "RawOptions",
    "JsonObject",
    "MemberOrUser",
    "Channel",
    "GuildChannel",
    "MessageableChannel",
    "MessageableGuildChannel",
    "ThreadableChannel",
    "ConnectableChannel",
    "ChannelTypeNames",
    "TextMessage",
    "TextReaction",
)


IDType: TypeAlias = int

GuildID: TypeAlias = IDType
CategoryID: TypeAlias = IDType
ChannelID: TypeAlias = IDType
ThreadID: TypeAlias = IDType
MessageID: TypeAlias = IDType
RoleID: TypeAlias = IDType
UserID: TypeAlias = IDType
ForumTagID: TypeAlias = IDType
AppCommandID: TypeAlias = IDType
EmojiID: TypeAlias = IDType
DiscordAutomodRuleID: TypeAlias = IDType

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
    TextChannel | ForumChannel | VoiceChannel | StageChannel | CategoryChannel
)
MessageableChannel: TypeAlias = (
    TextChannel | VoiceChannel | StageChannel | DMChannel | GroupChannel
)
MessageableGuildChannel: TypeAlias = TextChannel | VoiceChannel | StageChannel
ThreadableChannel: TypeAlias = TextChannel | ForumChannel
ConnectableChannel: TypeAlias = VoiceChannel | StageChannel

ChannelTypeNames: TypeAlias = Literal[
    "text",
    "news",
    "forum",
    "media",
    "news_thread",
    "public_thread",
    "private_thread",
    "voice",
    "stage_voice",
    "private",
    "group",
    "category",
]
"""
Contains all enumerator names from `discord.ChannelType`.

https://discordpy.readthedocs.io/en/latest/api.html#discord.ChannelType
"""

MemberFlagsNames: TypeAlias = Literal[
    "automod_quarantined_guild_tag",
    "automod_quarantined_username",
    "bypasses_verification",
    "completed_home_actions",
    "completed_onboarding",
    "did_rejoin",
    "dm_settings_upsell_acknowledged",
    "guest",
    "started_home_actions",
    "started_onboarding",
]
"""
Contains all member flag names from `discord.MemberFlags`

https://discordpy.readthedocs.io/en/latest/api.html#memberflags
"""

PublicUserFlagsNames: TypeAlias = Literal[
    "active_developer",
    "bot_http_interactions",
    "bug_hunter",
    "bug_hunter_level_2",
    "discord_certified_moderator",
    "early_supporter",
    "hypesquad",
    "hypesquad_balance",
    "hypesquad_bravery",
    "hypesquad_brilliance",
    "partner",
    "spammer",
    "staff",
    "system",
    "team_user",
    "verified_bot",
    "verified_bot_developer",
]
"""
Contains all public user flag names from `discord.PublicUserFlags`

https://discordpy.readthedocs.io/en/latest/api.html#publicuserflags
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
