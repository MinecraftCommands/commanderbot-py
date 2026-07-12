import string
from collections import defaultdict
from dataclasses import dataclass, field
from itertools import chain
from logging import Logger
from typing import TYPE_CHECKING, Any, Iterable, cast

from discord import Member, User
from discord.ext.commands import Bot
from discord.utils import format_dt, utcnow

from commanderbot.ext.automod.event import AutomodEvent
from commanderbot.ext.automod.types import ContextFields
from commanderbot.lib.predicates import is_member

__all__ = ("AutomodContext",)

if TYPE_CHECKING:
    from commanderbot.ext.automod.automod_guild_state import AutomodGuildState
    from commanderbot.ext.automod.rule import AutomodRule

SAFE_TYPES: tuple[type, ...] = (bool, int, float, str)


@dataclass
class AutomodContext:
    """
    The execution context that's given to all triggers, conditions, and actions.
    """

    bot: Bot
    log: Logger

    state: AutomodGuildState
    """The guild state that received the event."""

    rule: AutomodRule
    """The rule that's currently running."""

    event: AutomodEvent
    """The event that the rule is processing."""

    _metadata: dict[str, Any] = field(init=False, default_factory=dict)
    """Any additional data attached to the execution context."""

    def set_metadata(self, key: str, value: Any):
        """Add metadata to the execution context"""
        self._metadata[key] = value

    def remove_metadata(self, key: str):
        """Remove metadata from the execution context"""
        del self._metadata[key]

    def get_fields(self, *, unsafe: bool = False) -> dict[ContextFields, Any]:
        """Get the full context data as key/value pairs."""
        if unsafe:
            return dict(chain(self._yield_safe_fields(), self._yield_unsafe_fields()))  # type: ignore
        return dict(self._yield_safe_fields())  # type: ignore

    def format_content(
        self, content: str, *, default="`Unknown`", unsafe: bool = False
    ) -> str:
        """Format a string using context data."""
        fields: defaultdict[str, Any] = defaultdict(lambda: default)
        fields |= self.get_fields(unsafe=unsafe)

        template = string.Template(content)
        return template.safe_substitute(fields)

    def _is_value_safe(self, value: Any) -> bool:
        return type(value) in SAFE_TYPES

    def _yield_safe_fields(self) -> Iterable[tuple[str, Any]]:
        # Yield channel fields
        if channel := self.event.channel:
            yield ("channel_id", channel.id)
            yield ("channel_name", channel.name)
            yield ("channel_mention", channel.mention)

        # Yield thread fields
        if thread := self.event.thread:
            yield ("thread_id", thread.id)
            yield ("thread_name", thread.name)
            yield ("thread_mention", thread.mention)
            yield ("thread_archived", thread.archived)
            yield ("thread_locked", thread.locked)
            yield ("thread_slowmode_delay", thread.slowmode_delay)
            yield ("thread_auto_archive_duration", thread.auto_archive_duration)
            if thread_owner := thread.owner:
                yield from self._yield_safe_member_fields(thread_owner, "thread_owner")

        # Yield category fields
        if category := self.event.category:
            yield ("category_id", category.id)
            yield ("category_name", category.name)
            yield ("category_mention", category.mention)

        # Yield message fields
        if message := self.event.message:
            yield ("message_id", message.id)
            yield ("message_content", message.content)
            yield ("message_clean_content", message.clean_content)
            yield ("message_jump_url", message.jump_url)

        # Yield reaction fields
        if reaction := self.event.reaction:
            yield ("reaction_emoji", reaction.emoji)
            yield ("reaction_count", reaction.count)
            yield ("reaction_normal_count", reaction.normal_count)
            yield ("reaction_burst_count", reaction.burst_count)

        # Yield author fields
        if author := self.event.author:
            if is_member(author):
                yield from self._yield_safe_member_fields(author, "author")
            else:
                yield from self._yield_safe_user_fields(author, "author")

        # Yield actor fields
        if actor := self.event.actor:
            if is_member(actor):
                yield from self._yield_safe_member_fields(actor, "actor")
            else:
                yield from self._yield_safe_user_fields(actor, "actor")

        # Yield member fields
        if member := self.event.member:
            yield from self._yield_safe_member_fields(member, "member")

        # Yield user fields
        if user := self.event.user:
            yield from self._yield_safe_user_fields(user, "user")

        # Yield metadata fields
        yield from ((k, v) for k, v in self._metadata.items() if self._is_value_safe(v))

    def _yield_safe_user_fields(
        self, user: User, prefix: str
    ) -> Iterable[tuple[str, Any]]:
        yield (f"{prefix}_id", user.id)
        yield (f"{prefix}_name", user.name)
        yield (f"{prefix}_display_name", user.display_name)
        yield (f"{prefix}_mention", user.mention)
        yield (f"{prefix}_created_at", format_dt(user.created_at, style="R"))

    def _yield_safe_member_fields(
        self, member: Member, prefix: str
    ) -> Iterable[tuple[str, Any]]:
        yield from self._yield_safe_user_fields(cast(User, member), prefix)

        if nick := member.nick:
            yield (f"{prefix}_nick", nick)

        if joined_at := member.joined_at:
            yield (f"{prefix}_joined_at", format_dt(joined_at, style="R"))

            member_for = utcnow() - joined_at
            if member_for.days < 7:
                hh = int(member_for.total_seconds() / 3600)
                mm = int(member_for.total_seconds() / 60) % 60
                yield (f"{prefix}_member_for", f"{hh} hours, {mm} minutes")
            else:
                yield (f"{prefix}_member_for", f"{member_for.days} days")

    def _yield_unsafe_fields(self) -> Iterable[tuple[str, Any]]:
        if channel := self.event.channel:
            yield ("channel", channel)

        if thread := self.event.thread:
            yield ("thread", thread)

        if category := self.event.category:
            yield ("category", category)

        if message := self.event.message:
            yield ("message", message)

        if reaction := self.event.reaction:
            yield ("reaction", reaction)

        if author := self.event.author:
            yield ("author", author)

        if actor := self.event.actor:
            yield ("actor", actor)

        if member := self.event.member:
            yield ("member", member)

        if user := self.event.user:
            yield ("user", user)

        yield from (
            (k, v) for k, v in self._metadata.items() if not self._is_value_safe(v)
        )
