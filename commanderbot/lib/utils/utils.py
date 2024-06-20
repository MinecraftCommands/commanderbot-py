import asyncio
import ctypes
import io
import json
import os
import re
import traceback
from enum import Enum
from typing import (
    Any,
    AsyncIterable,
    Callable,
    Coroutine,
    Generator,
    Mapping,
    Optional,
    TypeVar,
    cast,
)

from discord import (
    AllowedMentions,
    AppInfo,
    Client,
    File,
    Interaction,
    Member,
    Message,
    PartialMessageable,
    User,
)
from discord.ext.commands import Bot, Context

from commanderbot.lib.type_predicates import (
    is_member,
    is_text_channel,
    is_thread,
    is_user,
)
from commanderbot.lib.types import MessageableChannel, RoleID, UserID

CHARACTER_CAP = 1900
INVITE_LINK_PATTERN = re.compile(
    r"(?:https?://)?discord(?:app)?\.(?:com/invite|gg)/[a-zA-Z0-9]+/?"
)
MESSAGE_LINK_PATTERN = re.compile(
    r"https?://(?:\w*\.)?discord(?:app)?\.com/channels/(\d+|@me)/(\d+)/(\d+)"
)
CUSTOM_EMOJI_PATTERN = re.compile(r"\<a?\:\w+\:\d+\>")

T = TypeVar("T")


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


def member_roles_from(member: User | Member, role_ids: set[RoleID]) -> set[RoleID]:
    """
    Return the set of matching member roles.
    A plain [User] may be passed, however an empty set will always be returned.
    """
    if is_user(member):
        return set()
    member_role_ids = {role.id for role in member.roles}
    matching_role_ids = role_ids.intersection(member_role_ids)
    return matching_role_ids


def dict_without_nones(d: Optional[Mapping[str, Any]] = None, **kwargs):
    dd = dict(d, **kwargs) if d else kwargs
    return {k: v for k, v in dd.items() if v is not None}


def dict_without_ellipsis(d: Optional[Mapping[str, Any]] = None, **kwargs):
    dd = dict(d, **kwargs) if d else kwargs
    return {k: v for k, v in dd.items() if v is not ...}


def dict_without_falsies(d: Optional[Mapping[str, Any]] = None, **kwargs):
    dd = dict(d, **kwargs) if d else kwargs
    return {k: v for k, v in dd.items() if v}


async def async_expand(it: AsyncIterable[T]) -> list[T]:
    return [value async for value in it]


async def async_schedule(
    *coroutines: Coroutine[Any, Any, Any] | Generator[Any, Any, Any]
):
    """
    Schedules a variable number of `Coroutine`s to run.

    Basically just a wrapper around an `asyncio.TaskGroup`.
    If an exception is raised, the `asyncio.TaskGroup` and `Coroutine`s will stop running.
    """
    async with asyncio.TaskGroup() as tg:
        for co in coroutines:
            tg.create_task(co)


def sanitize_stacktrace(error: Exception) -> str:
    lines = traceback.format_exception(
        type(error),
        value=error,
        tb=error.__traceback__,
    )

    def shorten(match):
        abs_path = match.group(1)
        basename = os.path.basename(abs_path)
        return f'File "{basename}"'

    lines = [re.sub(r'File "([^"]+)"', shorten, line, 1) for line in lines]

    return "".join(lines)


def format_context_cause(ctx: Context | Interaction) -> str:
    parts = []

    if author := (ctx.author if isinstance(ctx, Context) else ctx.user):
        parts.append(author.mention)
    else:
        parts.append("`Unknown User`")

    if channel := ctx.channel:
        if is_text_channel(channel) or is_thread(channel):
            parts.append(f"in {channel.mention}")
        else:
            parts.append(f"in channel `{channel}` (ID `{channel.id}`)")
    elif guild := ctx.guild:
        parts.append(f"in guild `{guild}` (ID `{guild.id}`)")

    return " ".join(parts)


def message_to_file(message: Message, filename: Optional[str] = None) -> File:
    filename = filename or "message.md"
    file_lines = []
    if message.content:
        file_lines.append(message.content)
    if message.attachments:
        file_lines += ["", "#### Attachments"]
        for att in message.attachments:
            att_json = json.dumps(att.to_dict(), indent=2)
            file_lines.append(f"\n```json\n{att_json}\n```")
    if message.embeds:
        file_lines += ["", "#### Embeds"]
        for embed in message.embeds:
            embed_json = json.dumps(embed.to_dict(), indent=2)
            file_lines.append(f"\n```json\n{embed_json}\n```")
    file_content = "\n".join(file_lines)
    fp = cast(Any, io.StringIO(file_content))
    file = File(fp=fp, filename=filename)
    return file


def str_to_file(contents: str, file_name: str) -> File:
    fp = cast(Any, io.StringIO(contents))
    return File(fp=fp, filename=file_name)


async def send_message_or_file(
    destination: MessageableChannel | PartialMessageable,
    content: str,
    *,
    file_callback: Callable[[], tuple[str, str, str]],
    allowed_mentions: AllowedMentions,
    character_cap: int = CHARACTER_CAP,
    **kwargs,
) -> Message:
    """
    Send `content` as a message if it fits, otherwise attach it as a file.

    Arguments
    ---------
    destination
        The destination (channel) to send the message (or upload the file) to.
    content
        The message content to send, if it fits.
    callback
        A callback to determine the alternate message content, file content, and file
        name in case a file needs to be uploaded instead. Note that the alternate
        message content should be guaranteed to fit within the message cap.
    character_cap
        The message character cap to check against, if different than the default.
    """
    if len(content) < character_cap:
        return await destination.send(content, allowed_mentions=allowed_mentions)
    else:
        alt_content, file_content, file_name = file_callback()
        fp = cast(Any, io.StringIO(file_content))
        file = File(fp=fp, filename=file_name)
        return await destination.send(
            alt_content,
            file=file,
            allowed_mentions=allowed_mentions,
            **kwargs,
        )


def is_int(value: Any):
    """
    Returns `True` if `value` can be casted to an int
    """
    try:
        int(value)
        return True
    except ValueError:
        return False


def is_float(value: Any):
    """
    Returns `True` if `value` can be casted to a float
    """
    try:
        float(value)
        return True
    except ValueError:
        return False


def pointer_size() -> int:
    """
    Returns the size of a pointer (in bits) for the system that Python is running on
    """
    return ctypes.sizeof(ctypes.c_void_p) * 8


class SizeUnit(Enum):
    KILOBYTE = 1
    MEGABYTE = 2
    GIGABYTE = 3
    TERRABYTE = 4
    PETABYTE = 5
    EXABYTE = 6
    ZETTABYTE = 7
    YOTTABYTE = 8


def bytes_to(n_bytes: int, to: SizeUnit, *, binary: bool = False) -> float:
    """
    Converts `n_bytes` to a different `SizeUnit`
    """
    divisor: float = 1024.0 if binary else 1000.0
    return n_bytes / (divisor**to.value)
