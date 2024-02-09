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
        feed: FeedType,
        channel_id: ChannelID,
        notification_role_id: Optional[RoleID],
        user_id: UserID,
    ) -> FeedsSubscription: ...

    async def modify(
        self,
        feed: FeedType,
        channel_id: ChannelID,
        notification_role_id: Optional[RoleID],
    ) -> FeedsSubscription: ...

    async def unsubscribe(
        self, feed: FeedType, channel_id: ChannelID
    ) -> FeedsSubscription: ...

    async def require_subscription(
        self, feed: FeedType, channel_id: ChannelID
    ) -> FeedsSubscription: ...

    async def get_subscription(
        self, feed: FeedType, channel_id: ChannelID
    ) -> Optional[FeedsSubscription]: ...

    def subscribers(self, feed: FeedType) -> AsyncIterable[FeedsSubscription]: ...
