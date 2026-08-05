from typing import Literal, override

from commanderbot.ext.automod import events
from commanderbot.ext.automod.automod_context import AutomodContext
from commanderbot.ext.automod.guards import IntegerRangeGuard
from commanderbot.ext.automod.trigger import AutomodTrigger
from commanderbot.lib.types import Timedelta

__all__ = ("MessageFrequency",)


class MessageFrequency(AutomodTrigger):
    """
    Triggers when a message author is a suspect of spamming.
    """

    type: Literal["message_frequency"]
    event_types = (events.MessageFrequency,)

    bucket: str
    """The bucket being used to track message frequency."""

    timeframe: Timedelta
    """How far back to consider a user's activity for spam."""

    message_count: IntegerRangeGuard
    """The number of messages a user must send before being suspected of spam."""

    channel_count: IntegerRangeGuard
    """
    The number of channels in which the user must send messages in before being suspected
    of spam.
    """

    @override
    async def ignore(self, context: AutomodContext) -> bool:
        # Ignore events dispatched by other buckets
        assert isinstance(context.event, events.MessageFrequency)
        bucket = context.event.bucket
        if bucket.name != self.bucket:
            return True

        # Build the message history out of our timeframe
        message = context.event.message
        since = message.created_at - self.timeframe
        message_history = bucket.build_message_history_since(message.author, since)

        # Ignore if the message history does not meet our thresholds
        enough_messages = self.message_count.includes(message_history.message_count)
        enough_channels = self.channel_count.includes(message_history.channel_count)
        return not (enough_messages and enough_channels)
