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
        channel_id: ChannelID,
        feed: FeedType,
        notification_role_id: Optional[RoleID],
        user_id: UserID,
    ) -> FeedsSubscription:
        cache = await self.db.get_cache()
        subscription = await cache.subscribe(
            channel_id, feed, notification_role_id, user_id
        )
        await self.db.dirty()
        return subscription

    # @implements FeedsStore
    async def modify(
        self,
        channel_id: ChannelID,
        feed: FeedType,
        notification_role_id: Optional[RoleID],
    ) -> FeedsSubscription:
        cache = await self.db.get_cache()
        subscription = await cache.modify(channel_id, feed, notification_role_id)
        await self.db.dirty()
        return subscription

    # @implements FeedsStore
    async def unsubscribe(
        self, channel_id: ChannelID, feed: FeedType
    ) -> FeedsSubscription:
        cache = await self.db.get_cache()
        subscription = await cache.unsubscribe(channel_id, feed)
        await self.db.dirty()
        return subscription

    # @implements FeedsStore
    async def require_subscription(
        self, channel_id: ChannelID, feed: FeedType
    ) -> FeedsSubscription:
        cache = await self.db.get_cache()
        return await cache.require_subscription(channel_id, feed)

    # @implements FeedsStore
    async def get_subscription(
        self, channel_id: ChannelID, feed: FeedType
    ) -> Optional[FeedsSubscription]:
        cache = await self.db.get_cache()
        return await cache.get_subscription(channel_id, feed)

    # @implements FeedsStore
    async def get_subscriptions(
        self, channel: ChannelID
    ) -> AsyncIterable[tuple[FeedType, FeedsSubscription]]:
        cache = await self.db.get_cache()
        async for subscription in cache.get_subscriptions(channel):
            yield subscription

    # @implements FeedsStore
    async def subscribers(self, feed: FeedType) -> AsyncIterable[FeedsSubscription]:
        cache = await self.db.get_cache()
        async for subscription in cache.subscribers(feed):
            yield subscription
