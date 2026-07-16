from typing import Literal, override

from discord import Thread
from pydantic import Field

from commanderbot.ext.automod.action import AutomodAction
from commanderbot.ext.automod.automod_context import AutomodContext
from commanderbot.lib.types import RoleID, UserID

__all__ = ("AddUsersToThread",)


class AddUsersToThread(AutomodAction):
    """
    Add users to the thread in context.
    """

    type: Literal["add_users_to_thread"]

    users: set[UserID] = Field(default_factory=set)
    """The users to add to the thread."""

    roles: set[RoleID] = Field(default_factory=set)
    """The roles to add to the thread. Any user with any of these roles will be added."""

    async def _try_add_user(
        self, context: AutomodContext, thread: Thread, user_id: UserID
    ):
        try:
            guild = thread.guild
            member = guild.get_member(user_id)
            assert member
            await thread.add_user(member)
        except:
            context.log.exception(
                f"Failed to add user '{user_id}' to thread '{thread.id}'"
            )

    async def _try_add_role(
        self, context: AutomodContext, thread: Thread, role_id: RoleID
    ):
        try:
            guild = thread.guild
            role = guild.get_role(role_id)
            assert role
            for member in role.members:
                await thread.add_user(member)
        except:
            context.log.exception(
                f"Failed to add role '{role_id}' to thread '{thread.id}'"
            )

    @override
    async def apply(self, context: AutomodContext):
        if thread := context.event.thread:
            if self.users:
                for user_id in self.users:
                    await self._try_add_user(context, thread, user_id)
            if self.roles:
                for role_id in self.roles:
                    await self._try_add_role(context, thread, role_id)
