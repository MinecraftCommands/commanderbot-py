from dataclasses import dataclass
from typing import AsyncIterable, Optional

from commanderbot.ext.feeds.feeds_data import FeedsData
from commanderbot.ext.feeds.feeds_store import FeedsSubscription
from commanderbot.ext.feeds.providers import FeedType
from commanderbot.lib import ChannelID, RoleID, UserID
from commanderbot.lib.cogs import CogStore
from commanderbot.lib.cogs.database import JsonFileDatabaseAdapter


# @implements FeedsStore
@dataclass
class FeedsJsonStore(CogStore):
    """
    Implementation of `FeedsStore` that uses a simple JSON file to persist state.
    """

    db: JsonFileDatabaseAdapter[FeedsData]

    # @implements FeedsStore
    async def subscribe(
        self,
        feed: FeedType,
        channel_id: ChannelID,
        notification_role_id: Optional[RoleID],
        user_id: UserID,
    ) -> FeedsSubscription:
        cache = await self.db.get_cache()
        subscription = await cache.subscribe(
            feed, channel_id, notification_role_id, user_id
        )
        await self.db.dirty()
        return subscription

    # @implements FeedsStore
    async def modify(
        self,
        feed: FeedType,
        channel_id: ChannelID,
        notification_role_id: Optional[RoleID],
    ) -> FeedsSubscription:
        cache = await self.db.get_cache()
        subscription = await cache.modify(feed, channel_id, notification_role_id)
        await self.db.dirty()
        return subscription

    # @implements FeedsStore
    async def unsubscribe(
        self, feed: FeedType, channel_id: ChannelID
    ) -> FeedsSubscription:
        cache = await self.db.get_cache()
        subscription = await cache.unsubscribe(feed, channel_id)
        await self.db.dirty()
        return subscription

    # @implements FeedsStore
    async def require_subscription(
        self, feed: FeedType, channel_id: ChannelID
    ) -> FeedsSubscription:
        cache = await self.db.get_cache()
        return await cache.require_subscription(feed, channel_id)

    # @implements FeedsStore
    async def get_subscription(
        self, feed: FeedType, channel_id: ChannelID
    ) -> Optional[FeedsSubscription]:
        cache = await self.db.get_cache()
        return await cache.get_subscription(feed, channel_id)

    # @implements FeedsStore
    async def subscribers(self, feed: FeedType) -> AsyncIterable[FeedsSubscription]:
        cache = await self.db.get_cache()
        async for subscription in cache.subscribers(feed):
            yield subscription
