from commanderbot.lib import ResponsiveException


class InviteException(ResponsiveException):
    pass


class InviteKeyAlreadyExists(InviteException):
    def __init__(self, key: str):
        self.key: str = key
        super().__init__(f"🤷 Invite key `{self.key}` already exists")


class InviteKeyMatchesExistingTag(InviteException):
    def __init__(self, key: str):
        self.key: str = key
        super().__init__(f"🤷 Invite key `{self.key}` matches an existing invite tag")


class InviteKeyMatchesOwnTag(InviteException):
    def __init__(self):
        super().__init__("🤷 An invite's tags can't contain the key")


class InviteTagMatchesExistingKey(InviteException):
    def __init__(self, tag: str):
        self.tag: str = tag
        super().__init__(f"🤷 Invite tag `{self.tag}` matches an existing invite key")


class InviteDoesNotExist(InviteException):
    def __init__(self, key: str):
        self.key: str = key
        super().__init__(f"😬 Invite `{self.key}` does not exist")


class GuildInviteNotSet(InviteException):
    def __init__(self):
        super().__init__("😬 An invite for this guild has not been set")


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
