from datetime import datetime

from commanderbot_lib.guild_state.abc.cog_guild_state import CogGuildState
from discord import Client, Message
from discord.ext.commands import Context

from commanderbot_ext.invite.invite_cache import InviteEntry
from commanderbot_ext.invite.invite_options import InviteOptions
from commanderbot_ext.invite.invite_store import (
    InviteStore,
    NotExistException,
    NotApplicableException,
    TagNameClashException,
    InviteNameException,
)


class InviteGuildState(CogGuildState[InviteOptions, InviteStore]):
    async def list_invites(self, ctx: Context):
        entries = await self.store.iter_guild_invites(self.guild)
        if len(entries) > 0:
            # Sort entries by name.
            sorted_entries = sorted(entries, key=lambda entry: entry.name)
            count = len(sorted_entries)
            invite_names = (entry.name for entry in sorted_entries)
            header = f"There are {count} invites available:\n```"
            if count == 1:
                header = f"There is 1 invite available:\n```"
            text = header + "\n".join(invite_names) + "\n```"
            await ctx.send(text)
        else:
            await ctx.send("There are no invites available")

    async def show_invite(self, ctx: Context, invite_query: str):
        if invite := self.store.get_invite_by_name(self.guild, invite_query):
            invite.hits += 1
            await ctx.send(invite.link)
        elif invites := self.store.get_invites_by_tag(self.guild, invite_query):
            for invite in invites:
                invite.hits += 1
                await ctx.send(invite.link)
        else:
            await ctx.send(f"No invite or tag exists called `{invite_query}`")

    async def add_invite(self, ctx: Context, link: str):
        name = (await ctx.bot.fetch_invite(link)).guild.name
        try:
            await self.store.add_invite(self.guild, name, link)
            await ctx.send(f"Added invite `{name}`")
        except InviteNameException as e:
            await ctx.send(
                f"An invite already exists under the name `{name}`:\n{e.existing.link}"
            )
        except TagNameClashException:
            await ctx.send(f"A tag already exists under the name `{name}`")

    async def update_invite(self, ctx: Context, name: str, link: str):
        try:
            new_name = (await ctx.bot.fetch_invite(link)).guild.name
            await self.store.update_invite(self.guild, name, link, new_name)
            await ctx.send(f"Updated invite `{name}`:\n{link}")
        except InviteNameException:
            await ctx.send(f"No invite exists called `{name}`")

    async def remove_invite(self, ctx: Context, name: str):
        try:
            await self.store.remove_invite(self.guild, name)
            await ctx.send(f"Invite `{name}` removed")
        except InviteNameException:
            await ctx.send(f"No invite exists called `{name}`")

    async def details(self, ctx: Context, name: str):
        if invite := self.store.get_invite_by_name(self.guild, name):
            await ctx.send(
                fr"""```{name}

Tags: {', '.join(invite.tags)}
Hits: {invite.hits}
Added On: {invite.added_on}
```
{invite.link}"""
            )
        else:
            await ctx.send(f"No invite exists called `{name}`")

    async def add_tag(self, ctx: Context, name: str, tag: str):
        try:
            await self.store.add_tag(self.guild, name, tag)
            await ctx.send(f"Added tag `{tag}` to invite {name}")
        except NotExistException:
            await ctx.send(f"No invite exists called `{name}`")
        except NotApplicableException:
            await ctx.send(f"Invite `{name}` already has tag `{tag}`")
        except TagNameClashException:
            await ctx.send(
                f"An invite already exists called `{tag}` so I can't use it as a tag"
            )

    async def remove_tag(self, ctx: Context, name: str, tag: str):
        try:
            await self.store.remove_tag(self.guild, name, tag)
            await ctx.send(f"Removed tag `{tag}` from invite {name}")
        except NotExistException:
            await ctx.send(f"No invite exists called `{name}`")
        except NotApplicableException:
            await ctx.send(f"Invite `{name}` doesn't have the tag `{tag}`")