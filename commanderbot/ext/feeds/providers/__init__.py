from enum import Enum

from commanderbot.ext.feeds.providers.minecraft_updates import *
from commanderbot.ext.feeds.providers.utils import *


class FeedProviderType(Enum):
    minecraft_java_updates = "Minecraft: Java Edition Updates"
    minecraft_bedrock_updates = "Minecraft: Bedrock Edition Updates"


class FeedType(Enum):
    minecraft_java_releases = "Minecraft: Java Edition Releases"
    minecraft_java_snapshots = "Minecraft: Java Edition Snapshots"
    minecraft_bedrock_releases = "Minecraft: Bedrock Edition Releases"
    minecraft_bedrock_previews = "Minecraft: Bedrock Edition Previews"
