import ctypes
import sys
from datetime import timedelta
from importlib.metadata import version

__all__ = (
    "BULK_DELETE_MAX_MESSAGES",
    "BULK_DELETE_MAX_MESSAGE_AGE",
    "COMMANDERBOT_VERSION",
    "DISCORD_PY_VERSION",
    "MAX_APPLICATION_EMOJIS",
    "MAX_AUTOCOMPLETE_CHOICES",
    "MAX_EMBED_DESCRIPTION_LENGTH",
    "MAX_EMBED_TITLE_LENGTH",
    "MAX_MESSAGE_LENGTH",
    "MAX_MODAL_TITLE_LENGTH",
    "POINTER_SIZE_BITS",
    "POINTER_SIZE_BYTES",
    "PYTHON_VERSION",
    "SUPPORTS_OCR",
    "USER_AGENT",
)

COMMANDERBOT_VERSION: str = version("commanderbot")
DISCORD_PY_VERSION: str = version("discord.py")
PYTHON_VERSION: str = (
    f"{sys.version_info[0]}.{sys.version_info[1]}.{sys.version_info[2]}"
)

try:
    import tesserocr  # noqa: F401 - Just checking if the import is available
except:
    SUPPORTS_OCR: bool = False
else:
    SUPPORTS_OCR: bool = True

USER_AGENT: str = (
    f"CommanderBuff/{COMMANDERBOT_VERSION} (By the Minecraft Commands community)"
)

MAX_MESSAGE_LENGTH: int = 2000
BULK_DELETE_MAX_MESSAGES: int = 100
BULK_DELETE_MAX_MESSAGE_AGE: timedelta = timedelta(days=14)

MAX_EMBED_TITLE_LENGTH: int = 256
MAX_EMBED_DESCRIPTION_LENGTH: int = 4096

MAX_MODAL_TITLE_LENGTH: int = 45

MAX_AUTOCOMPLETE_CHOICES: int = 25

MAX_APPLICATION_EMOJIS: int = 2000

POINTER_SIZE_BYTES: int = ctypes.sizeof(ctypes.c_void_p)
POINTER_SIZE_BITS: int = POINTER_SIZE_BYTES * 8
