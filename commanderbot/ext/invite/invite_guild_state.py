from dataclasses import dataclass
from typing import Iterable

from discord import Embed, Interaction, TextStyle
from discord.ui import TextInput
from discord.utils import format_dt

from commanderbot.ext.invite.invite_exceptions import QueryReturnedNoResults
from commanderbot.ext.invite.invite_store import InviteEntry, InviteStore
from commanderbot.lib import constants, utils
from commanderbot.lib.cogs import CogGuildState
from commanderbot.lib.cogs.views import CogStateModal
from commanderbot.lib.dialogs import ConfirmationResult, respond_with_confirmation


@dataclass
class InviteGuildState(CogGuildState):
    """
    Encapsulates the state and logic of the invite cog, at the guild level.

    Attributes
    -----------
    store
        The store used to interface with persistent data in a database-agnostic way.
    """

    store: InviteStore

    def _format_tags(self, tags: Iterable[str], *, delim: str = ",") -> str:
        return f"{delim} ".join((f"`{tag}`" for tag in tags))

    def _format_invite(self, entry: InviteEntry) -> str:
        if entry.description:
            return f"`{entry.key}` - {entry.description}"
        return f"`{entry.key}`"

    def _format_invite_line(self, entry: InviteEntry) -> str:
        if entry.description:
            return f"{entry.link} - {entry.description}"
        return entry.link

    async def get_invite(self, interaction: Interaction, query: str):
        if entries := await utils.async_expand(
            self.store.query_invites(self.guild, query)
        ):
            lines: list[str] = []
            for entry in entries:
                await self.store.increment_invite_hits(entry)
                lines.append(self._format_invite_line(entry))
            await interaction.response.send_message("\n".join(lines))
        else:
            raise QueryReturnedNoResults(query)

    async def list_invites(self, interaction: Interaction):
        # Get all invites and tags
        total_invites: int = 0
        all_descriptive_entries: list[InviteEntry] = []
        all_entries: list[InviteEntry] = []
        async for entry in self.store.get_invites(self.guild, sort=True):
            total_invites += 1
            if entry.description:
                all_descriptive_entries.append(entry)
            else:
                all_entries.append(entry)

        all_tags = await utils.async_expand(self.store.get_tags(self.guild, sort=True))

        # Format lines for embed description
        lines: list[str] = []
        if all_descriptive_entries or all_entries:
            lines.append("📩 **Invites**")

            # Add descriptive entries if they exist
            if all_descriptive_entries:
                entries_gen = (
                    f"• {self._format_invite(e)}" for e in all_descriptive_entries
                )
                lines.extend((*entries_gen, ""))

            # Add regular entries if they exist
            if all_entries:
                lines.extend(
                    (", ".join((self._format_invite(e) for e in all_entries)), "")
                )

            # Add tags if they exist
            if all_tags:
                lines.append(f"📦 **Tags**\n{self._format_tags(all_tags)}")

        # Create invite list embed
        embed = Embed(
            title="Available invites and tags",
            description="\n".join(lines) or "**None!**",
            color=0x00ACED,
        )
        embed.set_footer(text=f"Invites: {total_invites} | Tags: {len(all_tags)}")

        await interaction.response.send_message(embed=embed)

    async def get_guild_invite(self, interaction: Interaction):
        entry: InviteEntry = await self.store.require_guild_invite(self.guild)
        await self.store.increment_invite_hits(entry)
        await interaction.response.send_message(self._format_invite_line(entry))

    async def add_invite(self, interaction: Interaction):
        await interaction.response.send_modal(AddInviteModal(interaction, self))

    async def modify_invite(self, interaction: Interaction, invite: str):
        entry: InviteEntry = await self.store.require_invite(self.guild, invite)
        await interaction.response.send_modal(
            ModifyInviteModal(interaction, self, entry)
        )

    async def remove_invite(self, interaction: Interaction, invite: str):
        # Try to get the invite
        entry: InviteEntry = await self.store.require_invite(self.guild, invite)

        # Respond to this interaction with a confirmation dialog
        result: ConfirmationResult = await respond_with_confirmation(
            interaction,
            f"Are you sure you want to remove the invite `{entry.key}`?",
            timeout=10.0,
        )

        match result:
            case ConfirmationResult.YES:
                # If the answer was yes, attempt to remove the invite and send a response
                try:
                    await self.store.remove_invite(self.guild, entry.key)
                    await interaction.followup.send(
                        content=f"Removed the invite `{entry.key}`"
                    )
                except Exception as ex:
                    await interaction.delete_original_response()
                    raise ex
            case _:
                # If the answer was no, send a response
                await interaction.followup.send(
                    f"Did not remove the invite `{entry.key}`"
                )

    async def show_invite_details(self, interaction: Interaction, invite: str):
        # Try to get the invite
        entry: InviteEntry = await self.store.require_invite(self.guild, invite)

        # Format the tags so each tag is in an inline code block
        formatted_tags: str = self._format_tags(entry.sorted_tags) or "**None!**"

        # Create invite details embed
        embed = Embed(
            title=f"Details for invite `{entry.key}`",
            description=f"**Preview**\n> {self._format_invite_line(entry)}",
            color=0x00ACED,
        )
        embed.add_field(name="Key", value=f"`{entry.key}`", inline=False)
        embed.add_field(name="Tags", value=formatted_tags, inline=False)
        embed.add_field(name="Hits", value=f"`{entry.hits}`")
        embed.add_field(
            name="Added By",
            value=f"<@{entry.added_by_id}> ({format_dt(entry.added_on, style='R')})",
        )
        embed.add_field(
            name="Modified By",
            value=f"<@{entry.modified_by_id}> ({format_dt(entry.modified_on, style='R')})",
        )

        await interaction.response.send_message(embed=embed)

    async def set_guild_invite(self, interaction: Interaction, invite: str):
        entry: InviteEntry = await self.store.set_guild_invite(self.guild, invite)
        await interaction.response.send_message(
            f"Set invite `{entry.key}` as the invite for this guild"
        )

    async def clear_guild_invite(self, interaction: Interaction):
        await self.store.clear_guild_invite(self.guild)
        await interaction.response.send_message(f"Cleared the invite for this guild")

    async def show_guild_invite(self, interaction: Interaction):
        entry: InviteEntry = await self.store.require_guild_invite(self.guild)
        await interaction.response.send_message(
            f"Using invite `{entry.key}` as the invite for this guild"
        )


class InviteModal(CogStateModal[InviteGuildState, InviteStore]):
    """
    Base class for all invite modals
    """

    # Delimiter used between tag items
    delim: str = ","

    @classmethod
    def tags_from_str(cls, tags_str: str) -> list[str]:
        tag_gen = (tag.strip() for tag in tags_str.split(cls.delim))
        return [tag for tag in tag_gen if tag]

    @classmethod
    def tags_to_str(cls, tags: Iterable[str]) -> str:
        return f"{cls.delim} ".join(tags)


class AddInviteModal(InviteModal):
    def __init__(self, interaction: Interaction, state: InviteGuildState):
        super().__init__(
            interaction,
            state,
            title="Add a new invite",
            custom_id="commanderbot_ext:invite.add",
        )

        self.key_field = TextInput(
            label="Key",
            style=TextStyle.short,
            placeholder="Ex: sample-text",
            required=True,
        )
        self.tags_field = TextInput(
            label="Tags",
            style=TextStyle.short,
            placeholder="A comma separated list of tags. Ex: foo, bar, baz",
            required=False,
        )
        self.link_field = TextInput(
            label="Link",
            style=TextStyle.short,
            placeholder="Ex: https://discord.gg/...",
            required=True,
        )
        self.description_field = TextInput(
            label="Description (64 characters max)",
            style=TextStyle.short,
            placeholder="A short description about this invite.",
            max_length=64,
            required=False,
        )

        self.add_item(self.key_field)
        self.add_item(self.tags_field)
        self.add_item(self.link_field)
        self.add_item(self.description_field)

    async def on_submit(self, interaction: Interaction):
        entry: InviteEntry = await self.store.add_invite(
            guild=self.state.guild,
            key=self.key_field.value.strip(),
            tags=self.tags_from_str(self.tags_field.value),
            link=self.link_field.value.strip(),
            description=self.description_field.value.strip() or None,
            user_id=interaction.user.id,
        )
        await interaction.response.send_message(f"Added the invite `{entry.key}`")


class ModifyInviteModal(InviteModal):
    def __init__(
        self, interaction: Interaction, state: InviteGuildState, entry: InviteEntry
    ):
        # Get the invite key and also limit the modal title to 45 characters
        self.invite_key: str = entry.key
        title: str = f"Modifying invite: {entry.key}"
        if len(title) > constants.MAX_MODAL_TITLE_LENGTH:
            title = f"{title[:42]}..."

        super().__init__(
            interaction, state, title=title, custom_id="commanderbot_ext:invite.modify"
        )

        self.tags_field = TextInput(
            label="Tags",
            style=TextStyle.short,
            placeholder="A comma separated list of tags. Ex: foo, bar, baz",
            default=self.tags_to_str(entry.sorted_tags),
            required=False,
        )
        self.link_field = TextInput(
            label="Link",
            style=TextStyle.short,
            placeholder="Ex: https://discord.gg/...",
            default=entry.link,
            required=True,
        )
        self.description_field = TextInput(
            label="Description (64 characters max)",
            style=TextStyle.short,
            placeholder="A short description about this invite.",
            default=entry.description,
            max_length=64,
            required=False,
        )

        self.add_item(self.tags_field)
        self.add_item(self.link_field)
        self.add_item(self.description_field)

    async def on_submit(self, interaction: Interaction):
        entry: InviteEntry = await self.store.modify_invite(
            guild=self.state.guild,
            key=self.invite_key,
            tags=self.tags_from_str(self.tags_field.value),
            link=self.link_field.value.strip(),
            description=self.description_field.value.strip() or None,
            user_id=interaction.user.id,
        )
        await interaction.response.send_message(f"Modified the invite `{entry.key}`")
