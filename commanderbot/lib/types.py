from datetime import timedelta
from typing import Annotated, Any, Literal

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
    "AppCommandID",
    "AttachmentID",
    "CategoryID",
    "Channel",
    "ChannelID",
    "ChannelTypeNames",
    "ConnectableChannel",
    "DiscordAutomodRuleID",
    "EmojiID",
    "ForumTagID",
    "GuildChannel",
    "GuildID",
    "IDType",
    "JsonObject",
    "MemberOrUser",
    "MessageID",
    "MessageableChannel",
    "MessageableGuildChannel",
    "RawOptions",
    "RoleID",
    "TesseractLanguages",
    "TesseractScripts",
    "ThreadID",
    "ThreadableChannel",
    "Timedelta",
    "UnicodeNormalizationForms",
    "UserID",
)


type IDType = int

type GuildID = IDType
type CategoryID = IDType
type ChannelID = IDType
type ThreadID = IDType
type MessageID = IDType
type RoleID = IDType
type UserID = IDType
type ForumTagID = IDType
type AppCommandID = IDType
type EmojiID = IDType
type DiscordAutomodRuleID = IDType
type AttachmentID = IDType

type RawOptions = Any

type JsonObject = dict[str, Any]

type MemberOrUser = Member | User

type Channel = (
    TextChannel
    | ForumChannel
    | Thread
    | VoiceChannel
    | StageChannel
    | DMChannel
    | GroupChannel
    | CategoryChannel
)
type GuildChannel = (
    TextChannel | ForumChannel | VoiceChannel | StageChannel | CategoryChannel
)
type MessageableChannel = (
    TextChannel | VoiceChannel | StageChannel | DMChannel | GroupChannel
)
type MessageableGuildChannel = TextChannel | VoiceChannel | StageChannel
type ThreadableChannel = TextChannel | ForumChannel
type ConnectableChannel = VoiceChannel | StageChannel

type ChannelTypeNames = Literal[
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

type MemberFlagsNames = Literal[
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

type PublicUserFlagsNames = Literal[
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


type Timedelta = Annotated[
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
                    "pattern": r"^[+-]?P(?:(?:\d+W)|(?=.*(?:\d+[YMWDHMS]))(?:\d+Y)?(?:\d+M)?(?:\d+W)?(?:\d+D)?(?:T(?:\d+H(?:\d+M(?:\d+S)?)?|\d+M(?:\d+S)?|\d+S))?)",
                    "examples": ["PT5H30M", "PT2DT5H15M10S", "P2Y5M2W1DT4H20M"],
                },
                {
                    "type": "string",
                    "format": "duration",
                    "pattern": r"^[+-]?\s*(?:(?:\d+)\s*(?i:(?:days?|d))\s*,?\s*)?\d{2}:\d{2}:\d{2}(?:\.\d+)?$",
                    "examples": ["05:30:00", "2 days, 05:15:00", "5d, 04:20:00"],
                },
            ]
        },
        mode="validation",
    ),
]
"""
An alias for `datetime.timedelta`, but with a Json schema for Pydantic. 
"""

type UnicodeNormalizationForms = Literal["NFC", "NFD", "NFKC", "NFKD"]


# fmt: off
type TesseractLanguages = Literal[
    "afr", "amh", "ara", "asm", "aze", "aze_cyrl", "bel", "ben", "bod", "bos",
    "bre", "bul", "cat", "ceb", "ces", "chi_sim", "chi_sim_vert", "chi_tra", "chi_tra_vert", "chr",
    "cos", "cym", "dan", "deu", "deu_latf", "div", "dzo", "ell", "eng", "enm",
    "epo", "est", "eus", "fao", "fas", "fil", "fin", "fra", "frm", "fry",
    "gla", "gle", "glg", "grc", "guj", "hat", "heb", "hin", "hrv", "hun",
    "hye", "iku", "ind", "isl", "ita", "ita_old", "jav", "jpn", "jpn_vert", "kan",
    "kat", "kat_old", "kaz", "khm", "kir", "kmr", "kor", "kor_vert", "lao",
    "lat", "lav", "lit", "ltz", "mal", "mar", "mkd", "mlt", "mon", "mri",
    "msa", "mya", "nep", "nld", "nor", "oci", "ori", "pan", "pol", "por",
    "pus", "que", "ron", "rus", "san", "sin", "slk", "slv", "snd", "spa",
    "spa_old", "sqi", "srp", "srp_latn", "sun", "swa", "swe", "syr", "tam", "tat",
    "tel", "tgk", "tha", "tir", "ton", "tur", "uig", "ukr", "urd", "uzb",
    "uzb_cyrl", "vie", "yid", "yor",
]
"""
All languages that Tesseract supports (https://tesseract-ocr.github.io/tessdoc/Data-Files-in-different-versions.html).
"""
# fmt: on

# fmt: off
type TesseractScripts = Literal[
    "script/Arabic", "script/Armenian", "script/Bengali", "script/Canadian_Aboriginal", "script/Cherokee",
    "script/Cyrillic", "script/Devanagari", "script/Ethiopic", "script/Fraktur", "script/Georgian",
    "script/Greek", "script/Gujarati", "script/Gurmukhi", "script/Hangul", "script/Hangul_vert",
    "script/HanS", "script/HanS_vert", "script/HanT", "script/HanT_vert", "script/Hebrew",
    "script/Japanese", "script/Japanese_vert", "script/Kannada", "script/Khmer", "script/Lao",
    "script/Latin", "script/Malayalam", "script/Myanmar", "script/Oriya", "script/Sinhala",
    "script/Syriac", "script/Tamil", "script/Telugu", "script/Thaana", "script/Thai",
    "script/Tibetan", "script/Vietnamese",
]
"""
All scripts that Tesseract supports (https://tesseract-ocr.github.io/tessdoc/Data-Files-in-different-versions.html).
"""
# fmt: on
