from typing import Annotated

from pydantic import Field

from commanderbot.ext.automod import triggers

__all__ = ("AutomodTriggerType",)

type _AutomodTriggerType = (
    triggers.DiscordAutomodBlockedMemberInteractions
    | triggers.DiscordAutomodBlockedMessage
    | triggers.DiscordAutomodTimedOut
    | triggers.MemberBanned
    | triggers.MemberGainedFlags
    | triggers.MemberJoined
    | triggers.MemberLeft
    | triggers.MemberLostFlags
    | triggers.MemberTimeoutEnded
    | triggers.MemberTimeoutStarted
    | triggers.MemberTyping
    | triggers.MemberUnbanned
    | triggers.MentionsRemovedFromMessage
    | triggers.MessageDeleted
    | triggers.MessageEdited
    | triggers.MessageFrequency
    | triggers.MessageSent
    | triggers.Message
    | triggers.ReactionAdded
    | triggers.ReactionRemoved
    | triggers.Reaction
    | triggers.ThreadCreated
    | triggers.ThreadDeleted
)

type AutomodTriggerType = Annotated[_AutomodTriggerType, Field(discriminator="type")]
