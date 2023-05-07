from commanderbot.lib import ResponsiveException


class InviteException(ResponsiveException):
    pass


class InviteAlreadyExists(InviteException):
    def __init__(self, key: str):
        self.key: str = key
        super().__init__(f"🤷 Invite `{self.key}` already exists")


class InviteDoesNotExist(InviteException):
    def __init__(self, key: str):
        self.key: str = key
        super().__init__(f"😬 Invite `{self.key}` does not exist")


class GuildInviteNotSet(InviteException):
    def __init__(self):
        super().__init__(f"😬 An invite for this guild has not been set")


class QueryReturnedNoResults(InviteException):
    def __init__(self, query: str):
        self.query: str = query
        super().__init__(
            f"😔 Could not find any invites or tags matching `{self.query}`"
        )


class InvalidInviteLink(InviteException):
    def __init__(self, invite: str):
        self.invite: str = invite
        super().__init__(f"😬 `{self.invite}` is not a valid Discord invite link")
