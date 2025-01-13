from commanderbot.lib import ResponsiveException


class XKCDException(ResponsiveException):
    pass


class ComicNotFound(XKCDException):
    def __init__(self, num: int):
        super().__init__(f"😔 xkcd comic #{num} does not exist")
