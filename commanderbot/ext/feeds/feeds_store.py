from datetime import datetime
from typing import AsyncIterable, Optional, Protocol

from commanderbot.ext.feeds.providers import FeedType
from commanderbot.lib import ChannelID, RoleID, UserID


class FeedsSubscription(Protocol):
    channel_id: ChannelID
    notification_role_id: Optional[RoleID]
    subscriber_id: UserID
    subscribed_on: datetime


class FeedsStore(Protocol):
    async def subscribe(
        self,
        channel_id: ChannelID,
        feed: FeedType,
        notification_role_id: Optional[RoleID],
        user_id: UserID,
    ) -> FeedsSubscription: ...

    async def modify(
        self,
        channel_id: ChannelID,
        feed: FeedType,
        notification_role_id: Optional[RoleID],
    ) -> FeedsSubscription: ...

    async def unsubscribe(
        self, channel_id: ChannelID, feed: FeedType
    ) -> FeedsSubscription: ...

    async def require_subscription(
        self, channel_id: ChannelID, feed: FeedType
    ) -> FeedsSubscription: ...

    async def get_subscription(
        self, channel_id: ChannelID, feed: FeedType
    ) -> Optional[FeedsSubscription]: ...

    def get_subscriptions(
        self, channel: ChannelID
    ) -> AsyncIterable[tuple[FeedType, FeedsSubscription]]: ...

    def subscribers(self, feed: FeedType) -> AsyncIterable[FeedsSubscription]: ...
