from datetime import timedelta
from typing import Annotated, Any, Literal, TypeAlias

from discord import (
    CategoryChannel,
    DMChannel,
    ForumChannel,
    GroupChannel,
    Member,
    StageChannel,
    TextChannel,
    Thread,
    User,
    VoiceChannel,
)
from pydantic import WithJsonSchema

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
    "Timedelta",
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


Timedelta = Annotated[
    timedelta,
    WithJsonSchema(
        {
            "anyOf": [
                {
                    "type": "number",
                    "examples": [5, 1.0, 3.5],
                },
                {
                    "type": "string",
                    "format": "iso-8061-duration",
                    "pattern": r"^[+-]?P(?:(?:\d+W)|(?=.*(?:\d+[YMDHMS]))(?:\d+Y)?(?:\d+M)?(?:\d+D)?(?:T(?:\d+H(?:\d+M(?:\d+S)?)?|\d+M(?:\d+S)?|\d+S))?)$",
                    "examples": ["PT5H30M", "PT2DT5H15M10S", "P2Y5M2W1DT4H20M"],
                },
                {
                    "type": "string",
                    "format": "duration",
                    "pattern": r"^[+-]?\s*(?:(?:\d+)\s*(?i:(?:days?|d))\s*,?\s*)?\d{2}:\d{2}:\d{2}(?:\.\d+)?$",
                    "examples": ["05:30:00", "2 days, 5:15:00", "5d, 4:20:00"],
                },
            ]
        },
        mode="validation",
    ),
]
"""
An alias for `datetime.timedelta`, but with a Json schema for Pydantic. 
"""
