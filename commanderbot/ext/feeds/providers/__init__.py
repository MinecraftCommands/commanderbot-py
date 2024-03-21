from enum import Enum

from .minecraft_updates import *
from .utils import *


class FeedProviderType(Enum):
    MINECRAFT_JAVA_UPDATES = "Minecraft: Java Edition Updates"
    MINECRAFT_BEDROCK_UPDATES = "Minecraft: Bedrock Edition Updates"
    MINECRAFT_JAVA_JAR_UPDATES = "Minecraft: Java Edition Jar Updates"


class FeedType(Enum):
    MINECRAFT_JAVA_RELEASES = "Minecraft: Java Edition Releases"
    MINECRAFT_JAVA_SNAPSHOTS = "Minecraft: Java Edition Snapshots"
    MINECRAFT_BEDROCK_RELEASES = "Minecraft: Bedrock Edition Releases"
    MINECRAFT_BEDROCK_PREVIEWS = "Minecraft: Bedrock Edition Previews"
    MINECRAFT_JAVA_RELEASE_JARS = "Minecraft: Java Edition Release Jars"
    MINECRAFT_JAVA_SNAPSHOT_JARS = "Minecraft: Java Edition Snapshot Jars"
