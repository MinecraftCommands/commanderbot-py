from typing import Annotated

from pydantic import Field

from commanderbot.ext.automod import conditions

__all__ = ("AutomodConditionType",)

type _AutomodConditionType = (
    conditions.ActorAccountAge
    | conditions.ActorHasAllFlags
    | conditions.ActorHasAnyFlags
    | conditions.ActorIsBot
    | conditions.ActorIsNotBot
    | conditions.ActorMemberFor
    | conditions.ActorRoles
    | conditions.AllOf
    | conditions.AnyOf
    | conditions.AuthorAccountAge
    | conditions.AuthorHasAllFlags
    | conditions.AuthorHasAnyFlags
    | conditions.AuthorIsBot
    | conditions.AuthorIsNotBot
    | conditions.AuthorIsSelf
    | conditions.AuthorIsNotSelf
    | conditions.AuthorMemberFor
    | conditions.AuthorRoles
    | conditions.ImageAttachmentsContain
    | conditions.Inverted
    | conditions.MessageContentContains
    | conditions.MessageContentMatches
    | conditions.MessageHasAttachments
    | conditions.MessageHasEmbeds
    | conditions.MessageHasLinks
    | conditions.MessageHasMentions
    | conditions.MessageMentionsRoles
    | conditions.MessageMentionsUsers
    | conditions.NoneOf
    | conditions.RandomChance
    | conditions.Randomize
    | conditions.ReturnFalse
    | conditions.ReturnTrue
    | conditions.ThrowError
    | conditions.Wait
)

type AutomodConditionType = Annotated[
    _AutomodConditionType, Field(discriminator="type")
]
