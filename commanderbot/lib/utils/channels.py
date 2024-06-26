from typing import Optional

from discord import ForumChannel, ForumTag, Thread

from commanderbot.lib.predicates import is_convertable_to
from commanderbot.lib.types import ForumTagID

__all__ = (
    "format_forum_tag",
    "try_get_forum_tag",
    "require_forum_tag",
    "require_forum_tag_id",
    "thread_has_forum_tag_with_id",
)


def format_forum_tag(tag: ForumTag) -> str:
    """
    Returns a formatted string representation of a forum tag

    Formatted as either `"<name>"` or `"<emoji> <name>"`
    """
    return f"{tag.emoji} {tag.name}" if tag.emoji else tag.name


def try_get_forum_tag(
    forum: ForumChannel, tag_str: str, *, case_sensitive=False
) -> Optional[ForumTag]:
    """
    Returns a `ForumTag` if it exists in the forum
    """
    for tag in forum.available_tags:
        if case_sensitive and tag.name == tag_str:
            return tag
        elif tag.name.lower() == tag_str.lower():
            return tag
        elif is_convertable_to(tag_str, int) and tag.id == int(tag_str):
            return tag


def require_forum_tag(
    forum: ForumChannel, tag_str: str, *, case_sensitive=False
) -> ForumTag:
    if tag := try_get_forum_tag(forum, tag_str, case_sensitive=case_sensitive):
        return tag
    raise KeyError(f"Tag `{tag_str}` does not exist in <#{forum.id}>")


def require_forum_tag_id(forum: ForumChannel, id: ForumTagID) -> ForumTag:
    if tag := forum.get_tag(id):
        return tag
    raise KeyError(f"<#{forum.id}> does not have a tag with the ID `{id}`")


def thread_has_forum_tag_with_id(thread: Thread, id: ForumTagID) -> bool:
    applied_tags = (t.id for t in thread.applied_tags)
    return id in applied_tags
