from typing import Annotated

from pydantic import Field

from commanderbot.ext.automod import actions

__all__ = ("AutomodActionType",)

type _AutomodActionType = (
    actions.AddReactions
    | actions.AddRolesToActor
    | actions.AddRolesToAuthor
    | actions.AddToBucket
    | actions.AddUsersToThread
    | actions.DeleteActorMessages
    | actions.DeleteAuthorMessages
    | actions.DeleteMessage
    | actions.DMMember
    | actions.EditThread
    | actions.JoinThread
    | actions.LogMessage
    | actions.Randomize
    | actions.RemoveAllReactions
    | actions.RemoveOwnReactions
    | actions.RemoveReactions
    | actions.RemoveRolesFromActor
    | actions.RemoveRolesFromAuthor
    | actions.ReplyToMessage
    | actions.SendMessage
    | actions.Sequence
    | actions.ThrowError
    | actions.TimeoutActor
    | actions.TimeoutAuthor
    | actions.TypeInChannel
    | actions.Wait
)

type AutomodActionType = Annotated[_AutomodActionType, Field(discriminator="type")]
