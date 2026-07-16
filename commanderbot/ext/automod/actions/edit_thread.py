from typing import Annotated, Literal, Optional, override

from pydantic import Field

from commanderbot.ext.automod.action import AutomodAction
from commanderbot.ext.automod.automod_context import AutomodContext
from commanderbot.lib.types import ForumTagID
from commanderbot.lib.utils import dict_without_nones

__all__ = ("EditThread",)

type SlowmodeDelay = Annotated[int, Field(ge=0, le=21600)]
type AutoArchiveDuration = Literal[60, 1440, 4320, 10080]


class EditThread(AutomodAction):
    """
    Edit the thread in context.
    """

    type: Literal["edit_thread"]

    name: Optional[str] = None
    """The new name of the thread."""

    tags: set[ForumTagID] = Field(default_factory=set)
    """
    The new tags to apply to the thread. This only works if the thread is part of a forum.
    There can only be up to 5 tags applied to a thread.
    """

    pinned: Optional[bool] = None
    """Whether to pin the thread or not. This only works if the thread is part of a forum."""

    archived: Optional[bool] = None
    """Whether to archive the thread or not."""

    locked: Optional[bool] = None
    """Whether to lock the thread or not."""

    invitable: Optional[bool] = None
    """
    Whether non-moderators can add other non-moderators to the thread.
    Only available for private threads.
    """

    slowmode_delay: Optional[SlowmodeDelay] = None
    """
    Specifies the slowmode rate limit for users in the thread, in seconds.
    A value of `0` disables slowmode. The maximum value possible is `21600`.
    """

    auto_hide_duration: Optional[AutoArchiveDuration] = None
    """
    The new duration in minutes before a thread is automatically hidden
    from the channel list. Must be one of `60`, `1440`, `4320`, or `10080`.
    """

    reason: Optional[str] = None
    """The reason why the thread was edited, if any."""

    @override
    async def apply(self, context: AutomodContext):
        if thread := context.event.thread:
            params = dict_without_nones(
                name=self.name,
                applied_tags=self.tags,
                pinned=self.pinned,
                archived=self.archived,
                locked=self.locked,
                invitable=self.invitable,
                slowmode_delay=self.slowmode_delay,
                auto_archive_duration=self.auto_hide_duration,
                reason=self.reason,
            )
            await thread.edit(**params)
