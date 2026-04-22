from typing import Any, Optional

from discord import AllowedMentions, Interaction
from discord.ext.commands import Context
from pydantic_core import PydanticCustomError

__all__ = (
    "MalformedData",
    "NoSuchFactory",
    "InstantiationError",
    "ResponsiveException",
)


class MalformedData(Exception):
    def __init__(self, cls: type, data: Any):
        super().__init__(f"Cannot create {cls.__name__} from {type(data).__name__}")


class NoSuchFactory(PydanticCustomError):
    """
    Raised by a Pydantic validator if a factory function wasn't found.
    """

    def __init__(self, cls: type, factory_name: str):
        super().__init__(
            "no_such_factory",
            "'{class_name}' doesn't have a factory function called '{factory_name}'",
            {"class_name": cls.__name__, "factory_name": factory_name},
        )


class InstantiationError(PydanticCustomError):
    """
    Raised by a Pydantic validator if there was an error while instantiating a class.
    """

    def __init__(self, cls: type, exception: Exception):
        super().__init__(
            "instantiation_error",
            "An error occurred while instantiating a '{class_name}': {message}",
            {
                "class_name": cls.__name__,
                "message": str(exception),
            },
        )


class ResponsiveException(Exception):
    def __init__(
        self,
        *args,
        allowed_mentions: Optional[AllowedMentions] = None,
    ):
        self.allowed_mentions: Optional[AllowedMentions] = allowed_mentions
        super().__init__(*args)

    @classmethod
    def allowed_mentions_default_factory(cls) -> AllowedMentions:
        return AllowedMentions.none()

    async def respond(
        self,
        context: Context | Interaction,
        allowed_mentions: Optional[AllowedMentions] = None,
    ):
        allowed_mentions = (
            allowed_mentions
            or self.allowed_mentions
            or self.allowed_mentions_default_factory()
        )

        # Handle command errors
        if isinstance(context, Context):
            await context.message.reply(str(self), allowed_mentions=allowed_mentions)
            return

        # Handle app command errors that haven't had their interaction responded to
        if not context.response.is_done():
            await context.response.send_message(
                str(self), allowed_mentions=allowed_mentions, ephemeral=True
            )
            return

        # Handle app command errors that had their interaction responded to
        await context.followup.send(
            str(self), allowed_mentions=allowed_mentions, ephemeral=True
        )
