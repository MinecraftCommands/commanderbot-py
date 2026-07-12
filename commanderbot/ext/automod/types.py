from concurrent.futures import thread
from typing import Literal

__all__ = (
    "ContextEventFields",
    "ContextMetadataFields",
    "ContextFields",
)


type ContextEventFields = Literal[
    "channel_id",
    "channel_name",
    "channel_mention",

    "thread_id",
    "thread_name",
    "thread_mention",
    "thread_archived",
    "thread_locked",
    "thread_slowmode_delay",
    "thread_auto_archive_duration",
    "thread_owner",

    "category_id",
    "category_name",
    "category_mention",

    "message_id",
    "message_content",
    "message_clean_content",
    "message_jump_url",

    "reaction_emoji",
    "reaction_count",
    "reaction_normal_count",
    "reaction_burst_count",

    "author_id",
    "author_name",
    "author_display_name",
    "author_mention",
    "author_nick",
    "author_joined_at",
    "author_member_for",
    "author_created_at",

    "actor_id",
    "actor_name",
    "actor_display_name",
    "actor_mention",
    "actor_nick",
    "actor_joined_at",
    "actor_member_for",
    "actor_created_at",

    "member_id",
    "member_name",
    "member_display_name",
    "member_mention",
    "member_nick",
    "member_joined_at",
    "member_member_for",
    "member_created_at",

    "thread_owner_id",
    "thread_owner_name",
    "thread_owner_display_name",
    "thread_owner_mention",
    "thread_owner_nick",
    "thread_owner_joined_at",
    "thread_owner_member_for",
    "thread_owner_created_at",
    
    "user_id",
    "user_name",
    "user_display_name",
    "user_mention",
    "user_created_at",

    "channel"
    "thread"
    "category"
    "message"
    "reaction"
    "author"
    "actor"
    "member"
]

type ContextMetadataFields = Literal[
    "mentioned_roles",
    "mentioned_role_names",
    "mentioned_users",
    "mentioned_user_names",
    "removed_mentions",
    "removed_mention_names",
    "removed_user_mention_names",
    "removed_user_mentions",
    "removed_role_mentions",
    "removed_role_mention_names",
]

type ContextFields = ContextEventFields | ContextMetadataFields
