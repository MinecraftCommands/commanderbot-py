class MissingFeedHandler(Exception):
    def __init__(self):
        super().__init__("A valid feed handler couldn't be found or it wasn't assigned")


class UnknownMinecraftVersionFormat(Exception):
    def __init__(self, version: str):
        self.version: str = version
        super().__init__(f"Could not a find a Minecraft version in: `{self.version}`")
