from discord.ext.commands import Bot, Cog

from commanderbot.ext.feed.feed_options import FeedOptions
from commanderbot.ext.feed.providers import (
    MinecraftBedrockUpdates,
    MinecraftUpdateInfo,
)


class FeedCog(Cog, name="commanderbot.ext.feed"):
    def __init__(self, bot: Bot, **options):
        self.bot: Bot = bot
        self.options = FeedOptions.from_data(options)

        self.bedrock_updates = MinecraftBedrockUpdates.from_options(
            self.options.minecraft_bedrock_updates
        )
        self.bedrock_updates.release_handler = self.on_bedrock_release
        self.bedrock_updates.preview_handler = self.on_bedrock_preview

    async def cog_load(self):
        self.bedrock_updates.start()

    async def cog_unload(self):
        self.bedrock_updates.stop()

    async def on_bedrock_release(self, info: MinecraftUpdateInfo):
        print(info)

    async def on_bedrock_preview(self, info: MinecraftUpdateInfo):
        print(info)
