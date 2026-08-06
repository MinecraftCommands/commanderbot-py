import string
from collections import defaultdict
from collections.abc import Iterable
from dataclasses import asdict, dataclass, field
from itertools import chain
from logging import Logger
from typing import TYPE_CHECKING, Any, Optional, cast

import cv2
import imagehash
import numpy as np
from discord import Attachment, Member, User
from discord.ext.commands import Bot
from discord.utils import format_dt, utcnow
from imagehash import ImageHash
from mime_enum import MimeType, try_parse
from PIL import Image

from commanderbot.ext.automod.constants import IMAGE_MIME_TYPES
from commanderbot.ext.automod.event import AutomodEvent
from commanderbot.ext.automod.types import ContextAttachment
from commanderbot.lib.predicates import is_member
from commanderbot.lib.types import AttachmentID

__all__ = ("AutomodContext",)

if TYPE_CHECKING:
    from commanderbot.ext.automod.automod_guild_state import AutomodGuildState
    from commanderbot.ext.automod.rule import AutomodRule

SAFE_TYPES: tuple[type, ...] = (bool, int, float, str)


@dataclass
class AutomodContextMetadata:
    attachment_data: dict[AttachmentID, bytes] = field(default_factory=dict)
    image_attachment_phashes: dict[AttachmentID, ImageHash] = field(
        default_factory=dict
    )
    flagged_attachments: list[AttachmentID] = field(default_factory=list)
    mentioned_roles: Optional[str] = None
    mentioned_role_names: Optional[str] = None
    mentioned_users: Optional[str] = None
    mentioned_user_names: Optional[str] = None
    removed_mentions: Optional[str] = None
    removed_mention_names: Optional[str] = None
    removed_user_mention_names: Optional[str] = None
    removed_user_mentions: Optional[str] = None
    removed_role_mentions: Optional[str] = None
    removed_role_mention_names: Optional[str] = None


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

    metadata: AutomodContextMetadata = field(
        init=False, default_factory=AutomodContextMetadata
    )
    """Any additional data attached to the execution context."""

    async def fetch_attachments(self) -> list[ContextAttachment]:
        """
        Fetch all attachments from the execution context.

        This will also cache the attachment's data so it only needs to be
        fetched once.
        """

        # Return if we have no attachments in context
        if not self.event.attachments:
            return []

        attachments: list[ContextAttachment] = []
        for attachment in self.event.attachments:
            if data := self.metadata.attachment_data.get(attachment.id):
                phash = self.metadata.image_attachment_phashes.get(attachment.id)
                attachments.append((attachment, data, phash))
            elif result := await self._fetch_attachment(attachment):
                data, phash = result
                attachments.append((attachment, data, phash))
        return attachments

    async def fetch_attachments_with_type(
        self, *content_types: Optional[MimeType]
    ) -> list[ContextAttachment]:
        """
        Fetch all attachments from the execution context with a certain MIME types
        (https://en.wikipedia.org/wiki/Media_type#Types).

        This will also cache the attachment's data so it only needs to be
        fetched once.
        """

        # Return if we have no attachments in context
        if not self.event.attachments:
            return []

        attachments: list[ContextAttachment] = []
        for attachment in self.event.attachments:
            # Parse content type
            content_type: Optional[MimeType] = None
            if attachment.content_type is not None:
                content_type = try_parse(attachment.content_type)

            # Skip attachment if it has the wrong content type
            if content_type not in content_types:
                continue

            # Otherwise, get/fetch it
            if data := self.metadata.attachment_data.get(attachment.id):
                phash = self.metadata.image_attachment_phashes.get(attachment.id)
                attachments.append((attachment, data, phash))
            elif result := await self._fetch_attachment(attachment):
                data, phash = result
                attachments.append((attachment, data, phash))
        return attachments

    def _is_image_attachment(self, attachment: Attachment) -> bool:
        # Return if the attachment doesn't have a content type
        if attachment.content_type is None:
            return False

        # Parse content type
        content_type: Optional[MimeType] = try_parse(attachment.content_type)
        if content_type is None:
            return False

        # Check if the attachment is an image
        return content_type in IMAGE_MIME_TYPES

    async def _fetch_attachment(
        self, attachment: Attachment
    ) -> Optional[tuple[bytes, Optional[ImageHash]]]:
        if data := await self._fetch_attachment_data(attachment):
            # Store attachment data
            self.metadata.attachment_data[attachment.id] = data

            # Return early if this isn't an image attachment
            if not self._is_image_attachment(attachment):
                return (data, None)

            # Calculate phash
            buffer = np.frombuffer(data, np.uint8)
            image = cv2.imdecode(buffer, cv2.IMREAD_COLOR_RGB)
            assert image is not None
            
            image = Image.fromarray(image)
            phash = imagehash.phash(image)

            # Store image attachment phash
            self.metadata.image_attachment_phashes[attachment.id] = phash
            return (data, phash)

    async def _fetch_attachment_data(self, attachment: Attachment) -> Optional[bytes]:
        try:
            # Try fetching from the regular URL
            return await attachment.read()
        except Exception:
            pass

        try:
            # If that didn't work, try the proxy URL
            return await attachment.read(use_cached=True)
        except Exception:
            pass

    def get_fields(self, *, unsafe: bool = False) -> dict[str, Any]:
        """Get the full context data as key/value pairs."""
        if unsafe:
            return dict(chain(self._yield_safe_fields(), self._yield_unsafe_fields()))
        return dict(self._yield_safe_fields())

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
        yield from (
            (k, v) for k, v in asdict(self.metadata).items() if self._is_value_safe(v)
        )

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

        if attachments := self.event.attachments:
            yield ("attachments", attachments)

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
            (k, v)
            for k, v in asdict(self.metadata).items()
            if not self._is_value_safe(v)
        )
