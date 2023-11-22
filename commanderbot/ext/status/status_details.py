import re
from datetime import datetime, timedelta
from typing import Dict, Optional

from discord.ext.commands import Bot
from discord.utils import format_dt

from commanderbot.core.utils import check_commander_bot
from commanderbot.lib.constants import (
    COMMANDERBOT_VERSION,
    DISCORD_PY_VERSION,
    PYTHON_VERSION,
)


class StatusDetails:
    def __init__(self, bot: Bot):
        self.bot: Bot = bot

        # Store details about the bot
        self.python_version: str = PYTHON_VERSION
        self.discord_py_version: str = DISCORD_PY_VERSION
        self.commanderbot_version: str = COMMANDERBOT_VERSION

        # Store additional bot details, if available
        self.started_at: Optional[datetime] = None
        self.last_reconnect: Optional[datetime] = None
        self.uptime: Optional[timedelta] = None
        if cb := check_commander_bot(bot):
            self.started_at = cb.started_at
            self.last_reconnect = cb.connected_since
            self.uptime = cb.uptime

    def _format_timedelta(self, td: Optional[timedelta]) -> Optional[str]:
        if not td:
            return None

        times = [int(float(i)) for i in re.split("days?,|:", str(td))]
        if len(times) == 4:
            return f"{times[0]}d {times[1]}h {times[2]}m {times[3]}s"
        else:
            return f"0d {times[0]}h {times[1]}m {times[2]}s"

    @property
    def fields(self) -> Dict[str, str]:
        all_fields = {
            "Python version": f"`{self.python_version}`",
            "Discord.py version": f"`{self.discord_py_version}`",
            "CommanderBot version": f"`{self.commanderbot_version}`",
        }

        if dt := self.started_at:
            all_fields["Started"] = format_dt(dt, style="R")

        if dt := self.last_reconnect:
            all_fields["Last reconnect"] = format_dt(dt, style="R")

        if td := self.uptime:
            all_fields["Uptime"] = f"`{self._format_timedelta(td)}`"

        return all_fields
