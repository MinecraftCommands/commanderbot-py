from dataclasses import dataclass, field
from logging import Logger
from typing import Any, ClassVar, Iterable, Optional, Protocol, Type, cast

from discord import Member, TextChannel, Thread, User
from discord.ext.commands import Bot
from discord.utils import format_dt, utcnow

from commanderbot.lib import (
    ShallowFormatter,
    TextMessage,
    TextReaction,
    ValueFormatter,
    is_thread,
)


class AutomodEvent(Protocol):
    bot: Bot
    log: Logger

    @property
    def channel(self) -> Optional[TextChannel | Thread]:
        """Return the relevant channel, if any."""
        ...

    @property
    def thread(self) -> Optional[Thread]:
        """Return the relevant thread, if any."""
        ...

    @property
    def message(self) -> Optional[TextMessage]:
        """Return the relevant message, if any."""
        ...

    @property
    def reaction(self) -> Optional[TextReaction]:
        """Return the relevant reaction, if any."""
        ...

    @property
    def author(self) -> Optional[Member]:
        """Return the relevant author, if any."""
        ...

    @property
    def actor(self) -> Optional[Member]:
        """Return the acting user, if any."""
        ...

    @property
    def member(self) -> Optional[Member]:
        """Return the member-in-question, if any."""
        ...

    @property
    def user(self) -> Optional[User]:
        """Return the user-in-question, if any."""
        ...

    def set_metadata(self, key: str, value: Any):
        """Attach metadata to the event."""
        ...

    def remove_metadata(self, key: str):
        """Remove metadata from the event."""
        ...

    def get_fields(self, unsafe: bool = False) -> dict[str, Any]:
        """Get the full event data."""
        ...

    def format_content(self, content: str, *, unsafe: bool = False) -> str:
        """Format a string with event data."""
        ...


# @implements AutomodEvent
@dataclass
class AutomodEventBase:
    bot: Bot
    log: Logger

    _metadata: dict[str, Any] = field(init=False, default_factory=dict)

    SAFE_TYPES: ClassVar[tuple[Type, ...]] = (bool, int, float, str)

    def __init__(
        self,
        bot: Bot,
        log: Logger,
        **data: dict[str, Any],
    ) -> None:
        self.bot = bot
        self.log = log
        self._metadata = {}

    @property
    def channel(self) -> Optional[TextChannel | Thread]:
        return None

    @property
    def thread(self) -> Optional[Thread]:
        if is_thread(self.channel):
            return self.channel

    @property
    def message(self) -> Optional[TextMessage]:
        return None

    @property
    def reaction(self) -> Optional[TextReaction]:
        return None

    @property
    def author(self) -> Optional[Member]:
        return None

    @property
    def actor(self) -> Optional[Member]:
        return None

    @property
    def member(self) -> Optional[Member]:
        return None

    @property
    def user(self) -> Optional[User]:
        return cast(User, self.member)

    def set_metadata(self, key: str, value: Any):
        self._metadata[key] = value

    def remove_metadata(self, key: str):
        del self._metadata[key]

    def get_fields(self, unsafe: bool = False) -> dict[str, Any]:
        if unsafe:
            return self._get_fields_unsafe()
        return self._get_fields_safe()

    def format_content(self, content: str, *, unsafe: bool = False) -> str:
        # NOTE Beware of untrusted format strings!
        # Instead of providing a handful of library objects with arbitrary (and
        # potentially sensitive) data to the format string, we build a flattened set of
        # arguments and pass them to a safe formatter. Pass `unsafe=True` to explicitly
        # enable unsafe formatting for things like field access.
        fields = self.get_fields(unsafe)
        if unsafe:
            return content.format_map(fields)
        return ShallowFormatter().format(content, **fields)

    def _get_fields_unsafe(self) -> dict[str, Any]:
        format_args = self._get_fields_safe()
        format_args.update(
            channel=self.channel,
            message=self.message,
            reaction=self.reaction,
            author=self.author,
            actor=self.actor,
            member=self.member,
        )
        format_args.update(self._metadata)
        return format_args

    def _get_fields_safe(self) -> dict[str, Any]:
        return {k: v for k, v in self._yield_safe_fields()}

    def _is_value_safe(self, v: Any) -> bool:
        return (type(v) in self.SAFE_TYPES) or (
            isinstance(v, ValueFormatter) and (type(v.value) in self.SAFE_TYPES)
        )

    def _yield_safe_fields(self) -> Iterable[tuple[str, Any]]:
        if self.channel is not None:
            yield "channel_id", self.channel.id,
            yield "channel_name", self.channel.name,
            yield "channel_mention", self.channel.mention,
        if self.thread is not None:
            yield "thread_id", self.thread.id,
            yield "thread_name", self.thread.name,
            yield "thread_mention", self.thread.mention,
            yield "thread_archived", self.thread.archived,
            yield "thread_locked", self.thread.locked,
            yield "thread_slowmode_delay", self.thread.slowmode_delay,
            yield "thread_auto_archive_duration", self.thread.auto_archive_duration,
            if (thread_owner := self.thread.owner) is not None:
                yield from self._yield_safe_member_fields("thread_owner", thread_owner)
        if self.message is not None:
            yield "message_id", self.message.id
            yield "message_content", self.message.content
            yield "message_clean_content", self.message.clean_content
            yield "message_jump_url", self.message.jump_url
        if self.reaction is not None:
            yield "reaction_emoji", self.reaction.emoji
            yield "reaction_count", self.reaction.count
        if self.author is not None:
            yield from self._yield_safe_member_fields("author", self.author)
        if self.actor is not None:
            yield from self._yield_safe_member_fields("actor", self.actor)
        if self.member is not None:
            yield from self._yield_safe_member_fields("member", self.member)
        if self.user is not None:
            yield from self._yield_safe_user_fields("user", self.user)
        for k, v in self._yield_extra_fields():
            if self._is_value_safe(v):
                yield k, v
        for k, v in self._yield_metadata_fields():
            if self._is_value_safe(v):
                yield k, v

    def _yield_safe_member_fields(
        self, prefix: str, member: Member
    ) -> Iterable[tuple[str, Any]]:
        yield from self._yield_safe_user_fields(prefix, cast(User, member))
        yield f"{prefix}_nick", member.nick
        yield from self._yield_member_date_fields(prefix, member)

    def _yield_safe_user_fields(
        self, prefix: str, user: User
    ) -> Iterable[tuple[str, Any]]:
        yield f"{prefix}_id", user.id
        yield f"{prefix}_name", f"{user}"
        yield f"{prefix}_username", user.name
        yield f"{prefix}_discriminator", user.discriminator
        yield f"{prefix}_mention", user.mention
        yield f"{prefix}_display_name", user.display_name

    def _yield_member_date_fields(
        self, prefix: str, member: Member
    ) -> Iterable[tuple[str, Any]]:
        # joined_at
        joined_at_value = "Unknown"
        if joined_at := member.joined_at:
            joined_at_value = format_dt(joined_at, style="R")
        yield f"{prefix}_joined_at", ValueFormatter(joined_at_value)

        # member_for
        member_for_value = "Unknown"
        if joined_at := member.joined_at:
            member_for = utcnow() - joined_at
            member_for_str = f"{member_for.days} days"
            if member_for.days < 7:
                hh = int(member_for.total_seconds() / 3600)
                mm = int(member_for.total_seconds() / 60) % 60
                member_for_str = f"{hh} hours, {mm} minutes"
            member_for_value = member_for_str
        yield f"{prefix}_member_for", member_for_value

        # created_at
        yield f"{prefix}_created_at", ValueFormatter(
            format_dt(member.created_at, style="R")
        )

    def _yield_extra_fields(self) -> Iterable[tuple[str, Any]]:
        """Override this to provide additional fields based on the event type."""
        if False:
            yield

    def _yield_metadata_fields(self) -> Iterable[tuple[str, Any]]:
        for k, v in self._metadata.items():
            yield k, v
