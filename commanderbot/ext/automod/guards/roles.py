from typing import Iterable, Optional

from discord import Member, Role, User
from pydantic import BaseModel, ConfigDict, Field

from commanderbot.lib.predicates import is_member
from commanderbot.lib.types import RoleID

__all__ = ("RolesGuard",)


class RolesGuard(BaseModel):
    """
    Checks whether a role or a member's roles matches a set of roles.
    """

    model_config = ConfigDict(use_attribute_docstrings=True)

    include: set[RoleID] = Field(default_factory=set)
    """The roles to include. A role will match if it's in this set."""

    exclude: set[RoleID] = Field(default_factory=set)
    """
    The roles to exclude. A role will match if it's not in this set.
    """

    def _ignore_by_includes(self, roles: set[RoleID]) -> bool:
        if self.include:
            matching_role_ids = self.include.intersection(roles)
            return len(matching_role_ids) == 0
        return False

    def _ignore_by_excludes(self, roles: set[RoleID]) -> bool:
        if self.exclude:
            matching_role_ids = self.exclude.intersection(roles)
            return len(matching_role_ids) > 0
        return False

    def ignore(self, member: Optional[Member | User]) -> bool:
        """Determine whether to ignore the member based on their roles."""
        if not member:
            return False

        # Ignore users since they don't have roles
        if not is_member(member):
            return True

        roles = {role.id for role in member.roles}
        return self._ignore_by_includes(roles) or self._ignore_by_excludes(roles)

    def member_matches(self, member: User | Member) -> bool:
        if not is_member(member):
            return False

        # If `include` roles are defined, check if the member has *any* of them
        # Note that `include` takes precedence over `exclude`
        roles = {role.id for role in member.roles}
        if self.include:
            matching_role_ids = self.include.intersection(roles)
            return len(matching_role_ids) > 0

        # If `exclude` roles are defined, check if the member has *none* of them
        if self.exclude:
            matching_role_ids = self.exclude.intersection(roles)
            return len(matching_role_ids) == 0

        # If neither `include` nor `exclude` roles are defined, it's always a match
        return True

    def role_matches(self, role: Role) -> bool:
        if self.include:
            return role.id in self.include
        if self.exclude:
            return role.id not in self.exclude
        return True

    def filter_members(self, members: Iterable[User | Member]) -> list[User | Member]:
        """Filter a sequence of members based on the guard."""
        return [member for member in members if self.member_matches(member)]

    def filter_roles(self, roles: Iterable[Role]) -> list[Role]:
        """Filter a sequence of roles based on the guard."""
        return [role for role in roles if self.role_matches(role)]
