from pydantic import BaseModel

from commanderbot.lib.databases.json_db import JsonDBOptions


class AutomodOptions(BaseModel):
    database: JsonDBOptions
