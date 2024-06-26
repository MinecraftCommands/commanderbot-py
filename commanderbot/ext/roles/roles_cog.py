from typing import Any, Optional, cast

from discord import Member, Role
from discord.ext import commands
from discord.ext.commands import Bot, Cog, Context, Greedy

from commanderbot.ext.roles.roles_data import RolesData
from commanderbot.ext.roles.roles_guild_state import RolesGuildState
from commanderbot.ext.roles.roles_json_store import RolesJsonStore
from commanderbot.ext.roles.roles_options import RolesOptions
from commanderbot.ext.roles.roles_state import RolesState
from commanderbot.ext.roles.roles_store import RolesStore
from commanderbot.lib import is_guild, is_member
from commanderbot.lib.cogs import CogGuildStateManager
from commanderbot.lib.cogs.database import (
    InMemoryDatabaseOptions,
    JsonFileDatabaseAdapter,
    JsonFileDatabaseOptions,
    UnsupportedDatabaseOptions,
)
from commanderbot.lib.commands import LenientRoleConverter, checks


def make_roles_store(bot: Bot, cog: Cog, options: RolesOptions) -> RolesStore:
    db_options = options.database
    if isinstance(db_options, InMemoryDatabaseOptions):
        return RolesData()
    if isinstance(db_options, JsonFileDatabaseOptions):
        return RolesJsonStore(
            bot=bot,
            cog=cog,
            db=JsonFileDatabaseAdapter(
                options=db_options,
                serializer=lambda cache: cache.to_data(),
                deserializer=RolesData.from_data,
            ),
        )
    raise UnsupportedDatabaseOptions(db_options)


def member_has_permission():
    async def predicate(ctx: Context):
        cog = cast(RolesCog, ctx.cog)
        return (
            is_guild(ctx.guild)
            and is_member(ctx.author)
            and await cog.state[ctx.guild].member_has_permission(ctx.author)
        )

    return commands.check(predicate)


class RolesCog(Cog, name="commanderbot.ext.roles"):
    """
    Allows users to opt-in/out to/from configurable roles.

    Attributes
    ----------
    bot
        The bot/client instance this cog is attached to.
    options
        Immutable, pre-defined settings that define core cog behavior.
    store
        Abstracts the data storage and persistence of this cog.
    state
        Encapsulates the state and logic of this cog, for each guild.
    """

    def __init__(self, bot: Bot, **options):
        self.bot = bot
        self.options = RolesOptions.from_dict(options)
        self.store: RolesStore = make_roles_store(bot, self, self.options)
        self.state = RolesState(
            bot=self.bot,
            cog=self,
            guilds=CogGuildStateManager(
                bot=self.bot,
                cog=self,
                factory=lambda guild: RolesGuildState(
                    bot=bot, cog=self, guild=guild, store=self.store
                ),
            ),
            store=self.store,
        )

    def filter_unique_roles(self, roles: Any) -> list[Role]:
        return list({role: None for role in roles}.keys())

    def filter_unique_members(self, members: Any) -> list[Member]:
        return list({member: None for member in members}.keys())

    # @@ COMMANDS

    # @@ join

    @commands.command(
        name="join",
        brief="Join a role.",
    )
    @checks.guild_only()
    @checks.member_only()
    async def cmd_join(self, ctx: Context, *roles: LenientRoleConverter):
        unique_roles = self.filter_unique_roles(roles)
        assert is_guild(ctx.guild)
        await self.state[ctx.guild].join_roles(ctx, unique_roles)

    # @@ leave

    @commands.command(
        name="leave",
        brief="Leave a role.",
    )
    @checks.guild_only()
    @checks.member_only()
    async def cmd_leave(self, ctx: Context, *roles: LenientRoleConverter):
        unique_roles = self.filter_unique_roles(roles)
        assert is_guild(ctx.guild)
        await self.state[ctx.guild].leave_roles(ctx, unique_roles)

    # @@ roles

    @commands.group(
        name="roles",
        brief="Show relevant roles.",
    )
    @checks.guild_only()
    @checks.member_only()
    async def cmd_roles(self, ctx: Context):
        if not ctx.invoked_subcommand:
            assert is_guild(ctx.guild)
            await self.state[ctx.guild].show_relevant_roles(ctx)

    # @@ roles options

    @cmd_roles.group(
        name="options",
        brief="Configure extension options.",
    )
    @checks.is_guild_admin_or_bot_owner()
    @checks.member_only()
    async def cmd_roles_options(self, ctx: Context):
        if not ctx.invoked_subcommand:
            assert is_guild(ctx.guild)
            await ctx.send_help(self.cmd_roles_options)

    # @@ roles options permit

    @cmd_roles_options.group(
        name="permit",
        brief="Configure the set of roles permitted to add/remove other users to/from roles.",
    )
    async def cmd_roles_options_permit(self, ctx: Context):
        if not ctx.invoked_subcommand:
            if ctx.subcommand_passed:
                await ctx.send_help(self.cmd_roles_options_permit)
            else:
                assert is_guild(ctx.guild)
                await self.state[ctx.guild].show_permitted_roles(ctx)

    @cmd_roles_options_permit.command(
        name="show",
        brief="Show the roles permitted to add/remove other users to/from roles.",
    )
    async def cmd_roles_options_permit_show(self, ctx: Context):
        assert is_guild(ctx.guild)
        await self.state[ctx.guild].show_permitted_roles(ctx)

    @cmd_roles_options_permit.command(
        name="set",
        brief="Set the roles permitted to add/remove other users to/from roles.",
    )
    async def cmd_roles_options_permit_set(self, ctx: Context, *roles: Role):
        assert is_guild(ctx.guild)
        await self.state[ctx.guild].set_permitted_roles(ctx, *roles)

    @cmd_roles_options_permit.command(
        name="clear",
        brief="Clear all roles permitted to add/remove other users to/from roles.",
    )
    async def cmd_roles_options_permit_clear(self, ctx: Context):
        assert is_guild(ctx.guild)
        await self.state[ctx.guild].clear_permitted_roles(ctx)

    # @@ roles show

    @cmd_roles.command(
        name="show",
        brief="Show relevant roles.",
    )
    @checks.member_only()
    async def cmd_roles_show(self, ctx: Context):
        assert is_guild(ctx.guild)
        await self.state[ctx.guild].show_relevant_roles(ctx)

    # @@ roles about

    @cmd_roles.command(
        name="about",
        brief="Describe one or more roles.",
    )
    @checks.member_only()
    async def cmd_roles_about(self, ctx: Context, *roles: LenientRoleConverter):
        unique_roles = self.filter_unique_roles(roles)
        assert is_guild(ctx.guild)
        await self.state[ctx.guild].about_roles(ctx, unique_roles)

    # @@ roles join

    @cmd_roles.command(
        name="join",
        brief="Join one or more roles.",
    )
    @checks.member_only()
    async def cmd_roles_join(self, ctx: Context, *roles: LenientRoleConverter):
        unique_roles = self.filter_unique_roles(roles)
        assert is_guild(ctx.guild)
        await self.state[ctx.guild].join_roles(ctx, unique_roles)

    # @@ roles leave

    @cmd_roles.command(
        name="leave",
        brief="Leave one or more roles.",
    )
    @checks.member_only()
    async def cmd_roles_leave(self, ctx: Context, *roles: LenientRoleConverter):
        unique_roles = self.filter_unique_roles(roles)
        assert is_guild(ctx.guild)
        await self.state[ctx.guild].leave_roles(ctx, unique_roles)

    # @@ roles showall

    @cmd_roles.command(
        name="showall",
        brief="Show all roles.",
    )
    @checks.any_of(
        checks.is_administrator(),
        member_has_permission(),
        checks.is_owner(),
    )
    async def cmd_roles_showall(self, ctx: Context):
        assert is_guild(ctx.guild)
        await self.state[ctx.guild].show_all_roles(ctx)

    # @@ roles add

    @cmd_roles.command(
        name="add",
        brief="Add one or more roles to one or more members.",
    )
    @checks.any_of(
        checks.is_administrator(),
        member_has_permission(),
        checks.is_owner(),
    )
    @checks.member_only()
    async def cmd_roles_add(
        self, ctx: Context, roles: Greedy[LenientRoleConverter], *members: Member
    ):
        unique_roles = self.filter_unique_roles(roles)
        unique_members = self.filter_unique_members(members)
        assert is_guild(ctx.guild)
        await self.state[ctx.guild].add_roles_to_members(
            ctx, unique_roles, unique_members
        )

    # @@ roles remove

    @cmd_roles.command(
        name="remove",
        brief="Remove a role from members.",
    )
    @checks.any_of(
        checks.is_administrator(),
        member_has_permission(),
        checks.is_owner(),
    )
    @checks.member_only()
    async def cmd_roles_remove(
        self, ctx: Context, roles: Greedy[LenientRoleConverter], *members: Member
    ):
        unique_roles = self.filter_unique_roles(roles)
        unique_members = self.filter_unique_members(members)
        assert is_guild(ctx.guild)
        await self.state[ctx.guild].remove_roles_from_members(
            ctx, unique_roles, unique_members
        )

    # @@ roles register

    @cmd_roles.command(
        name="register",
        brief="Register a role.",
    )
    @checks.is_guild_admin_or_bot_owner()
    async def cmd_roles_register(
        self,
        ctx: Context,
        role: Role,
        joinable: bool = True,
        leavable: bool = True,
        *,
        description: Optional[str],
    ):
        assert is_guild(ctx.guild)
        await self.state[ctx.guild].register_role(
            ctx,
            role,
            joinable=joinable,
            leavable=leavable,
            description=description,
        )

    # @@ roles deregister

    @cmd_roles.command(
        name="deregister",
        brief="Deregister a role.",
    )
    @checks.is_guild_admin_or_bot_owner()
    async def cmd_roles_deregister(self, ctx: Context, role: Role):
        assert is_guild(ctx.guild)
        await self.state[ctx.guild].deregister_role(ctx, role)
