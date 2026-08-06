from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Literal, override

from discord import Member, Message, User
from discord.utils import utcnow
from pydantic import PrivateAttr

from commanderbot.ext.automod import events
from commanderbot.ext.automod.automod_context import AutomodContext
from commanderbot.ext.automod.bucket import AutomodBucket
from commanderbot.lib.types import ChannelID, MessageID, Timedelta, UserID

__all__ = ("MessageHistory",)


@dataclass
class MessageRecord:
    message_id: MessageID
    channel_id: ChannelID
    time: datetime


@dataclass
class ChannelRecord:
    channel_id: ChannelID
    messages: dict[MessageID, MessageRecord] = field(default_factory=dict)

    @property
    def message_count(self) -> int:
        return len(self.messages)

    def yield_messages(self) -> Iterable[MessageRecord]:
        yield from self.messages.values()


@dataclass
class UserRecord:
    user_id: UserID
    channels: dict[ChannelID, ChannelRecord] = field(default_factory=dict)

    @property
    def channel_count(self) -> int:
        return len(self.channels)

    @property
    def message_count(self) -> int:
        count: int = 0
        for channel_record in self.yield_channels():
            count += channel_record.message_count
        return count

    def yield_channels(self) -> Iterable[ChannelRecord]:
        yield from self.channels.values()

    def yield_messages(self) -> Iterable[MessageRecord]:
        for channel_record in self.yield_channels():
            yield from channel_record.yield_messages()

    def add_message_record(self, message_record: MessageRecord):
        """Add a message record to this user record."""
        channel_id = message_record.channel_id
        channel_record = self.channels.get(channel_id)
        if channel_record is None:
            channel_record = ChannelRecord(channel_id=channel_id)
            self.channels[channel_id] = channel_record
        message_id = message_record.message_id
        channel_record.messages[message_id] = message_record

    def add_message(self, message: Message):
        """Add a message to this user record."""
        message_record = MessageRecord(
            message_id=message.id,
            channel_id=message.channel.id,
            time=message.edited_at or message.created_at,
        )
        self.add_message_record(message_record)

    def add_from(self, other: UserRecord, since: datetime):
        """Add the message records of another user record to this user record."""
        for message_record in other.yield_messages():
            if message_record.time >= since:
                self.add_message_record(message_record)


type Partition = dict[UserID, UserRecord]
type History = defaultdict[datetime, Partition]


class MessageHistory(AutomodBucket):
    """
    Track message history across channels.
    """

    type: Literal["message_history"]

    lifetime: Timedelta
    """
    How long to record message history. Longer durations are able to record more
    message history for potential queries, but take more memory on average.
    """

    interval: Timedelta
    """
    The interval by which to partition message history. This is used to decide when to
    release old, unused message history and free memory.
    """

    _history: History = PrivateAttr(default_factory=lambda: defaultdict(dict))

    @property
    def lifetime_seconds(self) -> int:
        return int(self.lifetime.total_seconds())

    @property
    def interval_seconds(self) -> int:
        return int(self.lifetime.total_seconds())

    def _clean_up(self):
        cutoff = utcnow() - self.lifetime
        for interval in list(self._history.keys()):
            if interval < cutoff:
                del self._history[interval]

    def _to_interval(self, dt: datetime) -> datetime:
        ts = int(dt.timestamp())
        interval_ts = (ts // self.interval_seconds) * self.interval_seconds
        interval_dt = datetime.fromtimestamp(interval_ts, UTC)
        return interval_dt

    def yield_partitions_since(self, since_interval: datetime) -> Iterable[Partition]:
        for interval, partition in self._history.items():
            if interval >= since_interval:
                yield partition

    def yield_user_records_since(
        self, user: User | Member, since_interval: datetime
    ) -> Iterable[UserRecord]:
        for partition in self.yield_partitions_since(since_interval):
            if user_record := partition.get(user.id):
                yield user_record

    def build_message_history_since(
        self, user: User | Member, since: datetime
    ) -> UserRecord:
        message_history = UserRecord(user_id=user.id)
        since_interval = self._to_interval(since)
        for user_record in self.yield_user_records_since(user, since_interval):
            message_history.add_from(user_record, since)
        return message_history

    @override
    async def add(self, context: AutomodContext):
        # We need a message in context
        message = context.event.message
        if not message:
            return

        # Clean up expired message history
        self._clean_up()

        # Calculate the interval based on the most recent message timestamp, and use it
        # to get/create the corresponding partition.
        interval = self._to_interval(message.edited_at or message.created_at)
        partition = self._history[interval]

        # Within this partition, get/create the user's record
        user_id = message.author.id
        user_record = partition.get(user_id)
        if user_record is None:
            user_record = UserRecord(user_id=user_id)
            partition[user_id] = user_record
        user_record.add_message(message)

        # Dispatch events
        await context.state.dispatch_event(events.MessageFrequency(message, self))

    @override
    async def clear(self):
        self._history.clear()
