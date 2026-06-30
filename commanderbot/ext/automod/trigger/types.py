from typing import Annotated

from pydantic import Field

from commanderbot.ext.automod import triggers

__all__ = ("AutomodTriggerCollection",)

type AutomodTriggers = (
    triggers.DiscordAutomodBlockedMemberInteractions
    | triggers.DiscordAutomodBlockedMessage
    | triggers.DiscordAutomodTimedOut
    | triggers.MemberJoined
    | triggers.MemberLeft
    | triggers.MemberTyping
    | triggers.MentionsRemovedFromMessage
    | triggers.MemberGainedFlags
    | triggers.MemberLostFlags
    | triggers.MessageDeleted
    | triggers.MessageEdited
    | triggers.MessageSent
    | triggers.Message
    | triggers.Reaction
    | triggers.ReactionAdded
    | triggers.ReactionRemoved
    | triggers.ThreadCreated
    | triggers.ThreadDeleted
    | triggers.UserBanned
    | triggers.UserUnbanned
)

AutomodTriggerCollection = Annotated[
    list[Annotated[AutomodTriggers, Field(discriminator="type")]],
    Field(default_factory=list),
]
