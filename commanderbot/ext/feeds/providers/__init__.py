from enum import Enum

from commanderbot.ext.feeds.providers.minecraft_updates import *
from commanderbot.ext.feeds.providers.utils import *


class FeedProviderType(Enum):
    minecraft_java_updates = "Minecraft Java Updates"
    minecraft_bedrock_updates = "Minecraft Bedrock Updates"


class FeedType(Enum):
    minecraft_java_releases = "Minecraft Java Releases"
    minecraft_java_snapshots = "Minecraft Java Snapshots"
    minecraft_bedrock_releases = "Minecraft Bedrock Releases"
    minecraft_bedrock_previews = "Minecraft Bedrock Previews"
