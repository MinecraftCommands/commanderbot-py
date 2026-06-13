from pydantic import BaseModel

from commanderbot.lib.databases.json_db import JsonDBOptions


class HelpForumOptions(BaseModel):
    database: JsonDBOptions
