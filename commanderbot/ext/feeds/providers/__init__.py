from enum import Enum

from commanderbot.ext.feeds.providers.minecraft_updates import *
from commanderbot.ext.feeds.providers.utils import *


class FeedProviderType(Enum):
    MINECRAFT_JAVA_UPDATES = "Minecraft: Java Edition Updates"
    MINECRAFT_BEDROCK_UPDATES = "Minecraft: Bedrock Edition Updates"
    MINECRAFT_JAVA_JAR_UPDATES = "Minecraft: Java Edition JAR Updates"


class FeedType(Enum):
    MINECRAFT_JAVA_RELEASES = "Minecraft: Java Edition Releases"
    MINECRAFT_JAVA_SNAPSHOTS = "Minecraft: Java Edition Snapshots"
    MINECRAFT_BEDROCK_RELEASES = "Minecraft: Bedrock Edition Releases"
    MINECRAFT_BEDROCK_PREVIEWS = "Minecraft: Bedrock Edition Previews"
    MINECRAFT_JAVA_RELEASE_JARS = "Minecraft: Java Edition Release JARs"
    MINECRAFT_JAVA_SNAPSHOT_JARS = "Minecraft: Java Edition Snapshot JARs"
