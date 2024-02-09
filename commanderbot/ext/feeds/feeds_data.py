from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, AsyncIterable, Optional, Self

from discord.utils import utcnow

from commanderbot.ext.feeds.feeds_exceptions import (
    SubscriptionAlreadyExists,
    SubscriptionDoesNotExist,
)
from commanderbot.ext.feeds.feeds_store import FeedsSubscription
from commanderbot.ext.feeds.providers import FeedType
from commanderbot.lib import ChannelID, FromDataMixin, JsonSerializable, RoleID, UserID
from commanderbot.lib.utils import dict_without_falsies


@dataclass
class FeedsSubscriptionData(JsonSerializable, FromDataMixin):
    channel_id: ChannelID
    notification_role_id: Optional[RoleID]
    subscriber_id: UserID
    subscribed_on: datetime

    # @overrides FromDataMixin
    @classmethod
    def try_from_data(cls, data: Any) -> Optional[Self]:
        if isinstance(data, dict):
            return cls(
                channel_id=data["channel_id"],
                notification_role_id=data.get("notification_role_id"),
                subscriber_id=data["subscriber_id"],
                subscribed_on=datetime.fromisoformat(data["subscribed_on"]),
            )

    # @implements JsonSerializable
    def to_json(self) -> Any:
        return {
            "channel_id": self.channel_id,
            "notification_role_id": self.notification_role_id,
            "subscriber_id": self.subscriber_id,
            "subscribed_on": self.subscribed_on.isoformat(),
        }


@dataclass
class FeedsFeedData(JsonSerializable, FromDataMixin):
    subscribers: dict[ChannelID, FeedsSubscriptionData] = field(default_factory=dict)

    # @overrides FromDataMixin
    @classmethod
    def try_from_data(cls, data: Any) -> Optional[Self]:
        if isinstance(data, dict):
            subscribers = {}
            for raw_channel_id, raw_subscription in data.get("subscribers", {}).items():
                subscribers[int(raw_channel_id)] = FeedsSubscriptionData.from_data(
                    raw_subscription
                )
            return cls(subscribers=subscribers)

    # @implements JsonSerializable
    def to_json(self) -> Any:
        return dict_without_falsies(
            # Omit empty subscriptions
            subscribers=dict_without_falsies(
                {
                    str(channel_id): subscription.to_json()
                    for channel_id, subscription in self.subscribers.items()
                }
            ),
        )

    def require_subscription(self, channel_id: ChannelID) -> FeedsSubscriptionData:
        if subscription := self.subscribers.get(channel_id):
            return subscription
        raise SubscriptionDoesNotExist(channel_id)

    def get_subscription(
        self, channel_id: ChannelID
    ) -> Optional[FeedsSubscriptionData]:
        return self.subscribers.get(channel_id)

    def subscribe(
        self,
        channel_id: ChannelID,
        notification_role_id: Optional[RoleID],
        user_id: UserID,
    ) -> FeedsSubscriptionData:
        # Check if the subscription already exists
        if channel_id in self.subscribers:
            raise SubscriptionAlreadyExists(channel_id)

        # Create and add a new subscription
        subscription = FeedsSubscriptionData(
            channel_id, notification_role_id, user_id, utcnow()
        )
        self.subscribers[channel_id] = subscription
        return subscription

    def modify(
        self, channel_id: ChannelID, notification_role_id: Optional[RoleID]
    ) -> FeedsSubscriptionData:
        # The subscription must exist
        subscription = self.require_subscription(channel_id)

        # Modify the subscription
        subscription.notification_role_id = notification_role_id
        return subscription

    def unsubscribe(self, channel_id: ChannelID) -> FeedsSubscriptionData:
        # The subscription must exist
        subscription = self.require_subscription(channel_id)

        # Remove subscription
        del self.subscribers[channel_id]
        return subscription


# @implements FeedsStore
@dataclass
class FeedsData(JsonSerializable, FromDataMixin):
    """
    Implementation of `FeedsStore` using an in-memory object hierarchy.
    """

    mcje_releases: FeedsFeedData = field(default_factory=FeedsFeedData)
    mcje_snapshots: FeedsFeedData = field(default_factory=FeedsFeedData)
    mcbe_releases: FeedsFeedData = field(default_factory=FeedsFeedData)
    mcbe_previews: FeedsFeedData = field(default_factory=FeedsFeedData)

    # @overrides FromDataMixin
    @classmethod
    def try_from_data(cls, data: Any) -> Optional[Self]:
        if isinstance(data, dict):
            return cls(
                mcje_releases=FeedsFeedData.from_data(data.get("mcje_releases", {})),
                mcje_snapshots=FeedsFeedData.from_data(data.get("mcje_snapshots", {})),
                mcbe_releases=FeedsFeedData.from_data(data.get("mcbe_releases", {})),
                mcbe_previews=FeedsFeedData.from_data(data.get("mcbe_previews", {})),
            )

    # @implements JsonSerializable
    def to_json(self) -> Any:
        return dict_without_falsies(
            mcje_releases=self.mcje_releases.to_json(),
            mcje_snapshots=self.mcje_snapshots.to_json(),
            mcbe_releases=self.mcbe_releases.to_json(),
            mcbe_previews=self.mcbe_previews.to_json(),
        )

    def _get_feed(self, feed: FeedType) -> FeedsFeedData:
        match feed:
            case FeedType.minecraft_java_releases:
                return self.mcje_releases
            case FeedType.minecraft_java_snapshots:
                return self.mcje_snapshots
            case FeedType.minecraft_bedrock_releases:
                return self.mcbe_releases
            case FeedType.minecraft_bedrock_previews:
                return self.mcbe_previews
            case _:
                raise KeyError

    # @implements FeedsStore
    async def subscribe(
        self,
        feed: FeedType,
        channel_id: ChannelID,
        notification_role_id: Optional[RoleID],
        user_id: UserID,
    ) -> FeedsSubscription:
        feed_data = self._get_feed(feed)
        subscription = feed_data.subscribe(channel_id, notification_role_id, user_id)
        return subscription

    # @implements FeedsStore
    async def modify(
        self,
        feed: FeedType,
        channel_id: ChannelID,
        notification_role_id: Optional[RoleID],
    ) -> FeedsSubscription:
        feed_data = self._get_feed(feed)
        subscription = feed_data.modify(channel_id, notification_role_id)
        return subscription

    # @implements FeedsStore
    async def unsubscribe(
        self, feed: FeedType, channel_id: ChannelID
    ) -> FeedsSubscription:
        feed_data = self._get_feed(feed)
        subscription = feed_data.unsubscribe(channel_id)
        return subscription

    # @implements FeedsStore
    async def require_subscription(
        self, feed: FeedType, channel_id: ChannelID
    ) -> FeedsSubscription:
        feed_data = self._get_feed(feed)
        subscription = feed_data.require_subscription(channel_id)
        return subscription

    # @implements FeedsStore
    async def get_subscription(
        self, feed: FeedType, channel_id: ChannelID
    ) -> Optional[FeedsSubscription]:
        feed_data = self._get_feed(feed)
        subscription = feed_data.get_subscription(channel_id)
        return subscription

    # @implements FeedsStore
    async def subscribers(self, feed: FeedType) -> AsyncIterable[FeedsSubscription]:
        feed_data = self._get_feed(feed)
        for subscription in feed_data.subscribers.values():
            yield subscription
