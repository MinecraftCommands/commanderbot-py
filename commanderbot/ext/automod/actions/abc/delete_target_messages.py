from abc import abstractmethod
from itertools import islice
from typing import Optional, override

from discord import Object, User
from discord.utils import utcnow

from commanderbot.ext.automod import buckets
from commanderbot.ext.automod.action import AutomodAction
from commanderbot.ext.automod.automod_context import AutomodContext
from commanderbot.ext.automod.bucket import AutomodBucketRef
from commanderbot.lib.constants import (
    BULK_DELETE_MAX_MESSAGE_AGE,
    BULK_DELETE_MAX_MESSAGES,
)
from commanderbot.lib.predicates import is_messagable_guild_channel, is_thread
from commanderbot.lib.types import Timedelta

__all__ = ("DeleteTargetMessages",)


class DeleteTargetMessages(AutomodAction):
    bucket: AutomodBucketRef
    """The bucket being used to track message history."""

    previous_history: Timedelta
    """
    How much previous message history to delete. Note that due to Discord's limitations, you can't delete 
    more than 100 messages in each channel and the messages can't be more than 14 days old.
    """

    @abstractmethod
    def get_target(self, context: AutomodContext) -> Optional[User]:
        ...

    @override
    async def apply(self, context: AutomodContext):
        if target := self.get_target(context):
            bucket = await self.bucket.resolve(context, buckets.MessageHistory)

            since = utcnow() - min(self.previous_history, BULK_DELETE_MAX_MESSAGE_AGE)
            message_history = bucket.build_message_history_since(target, since)

            for channel_record in message_history.yield_channels():
                channel_id = channel_record.channel_id
                channel = context.bot.get_channel(channel_id)
                assert is_messagable_guild_channel(channel) or is_thread(channel)

                messages = islice(
                    channel_record.yield_messages(),
                    BULK_DELETE_MAX_MESSAGES,
                )
                to_delete = (Object(id=m.message_id) for m in messages)

                try:
                    await channel.delete_messages(to_delete)
                except:
                    pass 
