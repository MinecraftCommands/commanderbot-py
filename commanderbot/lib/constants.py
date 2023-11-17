import sys
from importlib.metadata import version

__all__ = (
    "COMMANDERBOT_VERSION",
    "DISCORD_PY_VERSION",
    "PYTHON_VERSION",
    "USER_AGENT",
    "MAX_MESSAGE_LENGTH",
    "MAX_EMBED_TITLE_LENGTH",
    "MAX_EMBED_DESCRIPTION_LENGTH",
    "MAX_AUTOCOMPLETE_CHOICES",
)

COMMANDERBOT_VERSION: str = version("commanderbot")
DISCORD_PY_VERSION: str = version("discord.py")
PYTHON_VERSION: str = (
    f"{sys.version_info[0]}.{sys.version_info[1]}.{sys.version_info[2]}"
)

USER_AGENT: str = (
    f"CommanderBuff/{COMMANDERBOT_VERSION} (By the Minecraft Commands community)"
)

MAX_MESSAGE_LENGTH: int = 2000

MAX_EMBED_TITLE_LENGTH: int = 256
MAX_EMBED_DESCRIPTION_LENGTH: int = 4096

MAX_AUTOCOMPLETE_CHOICES: int = 25
