from discord.ext.commands import Bot, Cog

from commanderbot.ext.feeds.feeds_options import FeedsOptions
from commanderbot.ext.feeds.providers import (
    MinecraftBedrockUpdates,
    MinecraftJavaUpdates,
    MinecraftUpdateInfo,
)


class FeedsCog(Cog, name="commanderbot.ext.feeds"):
    def __init__(self, bot: Bot, **options):
        self.bot: Bot = bot
        self.options = FeedsOptions.from_data(options)

        self.java_updates = MinecraftJavaUpdates.from_options(
            self.options.minecraft_java_updates
        )
        self.bedrock_updates = MinecraftBedrockUpdates.from_options(
            self.options.minecraft_bedrock_updates
        )

        self.java_updates.release_handler = self.on_java_release
        self.java_updates.snapshot_handler = self.on_java_snapshot
        self.bedrock_updates.release_handler = self.on_bedrock_release
        self.bedrock_updates.preview_handler = self.on_bedrock_preview

    async def cog_load(self):
        self.java_updates.start()
        self.bedrock_updates.start()

    async def cog_unload(self):
        self.java_updates.stop()
        self.bedrock_updates.stop()

    async def on_java_release(self, info: MinecraftUpdateInfo):
        print(f"Java release: {info}")

    async def on_java_snapshot(self, info: MinecraftUpdateInfo):
        print(f"Java snapshot: {info}")

    async def on_bedrock_release(self, info: MinecraftUpdateInfo):
        print(f"Bedrock release: {info}")

    async def on_bedrock_preview(self, info: MinecraftUpdateInfo):
        print(f"Bedrock preview: {info}")
