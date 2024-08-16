from dataclasses import dataclass
from typing import AsyncIterable, Optional

from discord import ChannelType

from commanderbot.ext.feeds.feeds_data import FeedsData
from commanderbot.ext.feeds.feeds_store import FeedsSubscription
from commanderbot.ext.feeds.providers import FeedType
from commanderbot.lib import ChannelID, MessageID, RoleID, UserID
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
        channel_type: ChannelType,
        feed: FeedType,
        notification_role_id: Optional[RoleID],
        auto_pin: bool,
        user_id: UserID,
    ) -> FeedsSubscription:
        cache = await self.db.get_cache()
        subscription = await cache.subscribe(
            channel_id, channel_type, feed, notification_role_id, auto_pin, user_id
        )
        await self.db.dirty()
        return subscription

    # @implements FeedsStore
    async def modify(
        self,
        channel_id: ChannelID,
        feed: FeedType,
        notification_role_id: Optional[RoleID],
        auto_pin: bool,
    ) -> FeedsSubscription:
        cache = await self.db.get_cache()
        subscription = await cache.modify(
            channel_id, feed, notification_role_id, auto_pin
        )
        await self.db.dirty()
        return subscription

    # @implements FeedsStore
    async def update_current_pin(
        self, subscription: FeedsSubscription, pin_id: MessageID
    ):
        cache = await self.db.get_cache()
        await cache.update_current_pin(subscription, pin_id)
        await self.db.dirty()

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
