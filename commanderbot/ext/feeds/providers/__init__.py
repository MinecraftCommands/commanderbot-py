from enum import Enum

from commanderbot.ext.feeds.providers.minecraft_updates import *


class FeedType(Enum):
    minecraft_java_releases = "MinecraftJavaUpdates.Releases"
    minecraft_java_snapshots = "MinecraftJavaUpdates.Snapshots"
    minecraft_bedrock_releases = "MinecraftBedrockUpdates.Releases"
    minecraft_bedrock_previews = "MinecraftBedrockUpdates.Previews"
