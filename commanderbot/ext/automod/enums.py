from enum import StrEnum

from discord.app_commands import Choice

__all__ = ("BucketTypeChoices",)


class BucketTypeChoices(StrEnum):
    FLAGGED_IMAGE_ATTACHMENTS = "flagged_image_attachments"
    MESSAGE_HISTORY = "message_history"

    @classmethod
    def as_choices(cls) -> list[Choice[str]]:
        return [Choice(name=e.value, value=e.value) for e in cls]
