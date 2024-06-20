import re
from dataclasses import dataclass
from typing import Iterable, Optional

from discord import AllowedMentions, Embed, Interaction, Message, TextStyle
from discord.ui import TextInput
from discord.utils import format_dt

from commanderbot.ext.faq.faq_exceptions import QueryReturnedNoResults
from commanderbot.ext.faq.faq_options import FaqOptions
from commanderbot.ext.faq.faq_store import FaqEntry, FaqStore
from commanderbot.lib import (
    ConfirmationResult,
    constants,
    respond_with_confirmation,
    utils,
)
from commanderbot.lib.cogs import CogGuildState
from commanderbot.lib.cogs.views import CogStateModal


@dataclass
class FaqGuildState(CogGuildState):
    """
    Encapsulates the state and logic of the faq cog, at the guild level.

    Attributes
    -----------
    store
        The store used to interface with persistent data in a database-agnostic way.
    """

    store: FaqStore
    options: FaqOptions

    async def _query_faq(self, query: str) -> FaqEntry:
        # Try to get the faq by its key or alias
        if entry := await self.store.query_faq(self.guild, query):
            return entry

        # If no faq was found, raise an exception with suggestions
        suggestions_gen = self.store.query_faqs_by_terms(
            self.guild, query, sort=True, cap=self.options.term_cap
        )
        suggestions: list[str] = await utils.async_expand(
            (entry.key async for entry in suggestions_gen)
        )
        raise QueryReturnedNoResults(query, *suggestions)

    async def on_message(self, message: Message):
        content: str = message.content
        prefix_pattern: Optional[re.Pattern] = await self.store.get_prefix_pattern(
            self.guild
        )
        match_pattern: Optional[re.Pattern] = await self.store.get_match_pattern(
            self.guild
        )

        # Check if the prefix pattern is being used and get faqs using it
        if (
            self.options.allow_prefix
            and prefix_pattern
            and (match := prefix_pattern.match(content))
        ):
            try:
                query: str = "".join(match.groups())
                entry: FaqEntry = await self._query_faq(query)
                await self.store.increment_faq_hits(entry)
                await message.channel.send(
                    entry.content, allowed_mentions=AllowedMentions.none()
                )
            except QueryReturnedNoResults as ex:
                await message.channel.send(str(ex))
            return

        # Otherwise scan the message using the match pattern, if any
        if self.options.allow_match and match_pattern:
            entries_gen = self.store.query_faqs_by_match(
                self.guild, content, cap=self.options.match_cap
            )
            async for entry in entries_gen:
                await self.store.increment_faq_hits(entry)
                await message.channel.send(
                    entry.content, allowed_mentions=AllowedMentions.none()
                )

    async def get_faq(self, interaction: Interaction, query: str):
        entry: FaqEntry = await self._query_faq(query)
        await self.store.increment_faq_hits(entry)
        await interaction.response.send_message(
            entry.content, allowed_mentions=AllowedMentions.none()
        )

    async def list_faqs(self, interaction: Interaction):
        # Get all faqs and format them
        entries: list[FaqEntry] = await utils.async_expand(
            self.store.get_faqs(self.guild, sort=True)
        )
        formatted_entries: str = ", ".join((f"`{entry.key}`" for entry in entries))

        # Create faq list embed
        embed = Embed(
            title="Available FAQs",
            description=formatted_entries or "**None!**",
            color=0x00ACED,
        )
        embed.set_footer(text=f"FAQs: {len(entries)}")

        await interaction.response.send_message(embed=embed)

    async def add_faq(self, interaction: Interaction):
        await interaction.response.send_modal(AddFaqModal(interaction, self))

    async def modify_faq(self, interaction: Interaction, faq: str):
        entry: FaqEntry = await self.store.require_faq(self.guild, faq)
        await interaction.response.send_modal(ModifyFaqModal(interaction, self, entry))

    async def remove_faq(self, interaction: Interaction, faq: str):
        # Try to get the faq
        entry: FaqEntry = await self.store.require_faq(self.guild, faq)

        # Respond to this interaction with a confirmation dialog
        result: ConfirmationResult = await respond_with_confirmation(
            interaction,
            f"Are you sure you want to remove the FAQ `{entry.key}`?",
            timeout=10.0,
        )

        match result:
            case ConfirmationResult.YES:
                # If the answer was yes, attempt to remove the faq and send a response
                try:
                    await self.store.remove_faq(self.guild, entry.key)
                    await interaction.followup.send(
                        content=f"Removed FAQ: `{entry.key}`"
                    )
                except Exception as ex:
                    await interaction.delete_original_response()
                    raise ex
            case _:
                # If the answer was no, send a response
                await interaction.followup.send(f"Did not remove FAQ: `{entry.key}`")

    async def show_faq_details(self, interaction: Interaction, faq: str):
        # Try to get the faq
        entry: FaqEntry = await self.store.require_faq(self.guild, faq)

        # Format faq data
        formatted_content: str = "\n".join(
            (f"> {line}" for line in entry.content.split("\n"))
        )
        formatted_aliases: str = (
            f", ".join((f"`{alias}`" for alias in entry.sorted_aliases)) or "**None!**"
        )
        formatted_tags: str = (
            f", ".join((f"`{tag}`" for tag in entry.sorted_tags)) or "**None!**"
        )

        # Create faq details embed
        embed = Embed(
            title=f"Details for FAQ `{entry.key}`",
            description=f"**Preview**\n{formatted_content}",
            color=0x00ACED,
        )
        embed.add_field(name="Key", value=f"`{entry.key}`", inline=False)
        embed.add_field(name="Aliases", value=formatted_aliases, inline=False)
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

    async def set_prefix_pattern(self, interaction: Interaction, prefix: str):
        pattern: re.Pattern = await self.store.set_prefix_pattern(self.guild, prefix)
        await interaction.response.send_message(
            f"Set the FAQ prefix pattern to: ```\n{pattern.pattern}\n```"
        )

    async def clear_prefix_pattern(self, interaction: Interaction):
        await self.store.clear_prefix_pattern(self.guild)
        await interaction.response.send_message("Cleared the FAQ prefix pattern")

    async def show_prefix_pattern(self, interaction: Interaction):
        pattern: re.Pattern = await self.store.require_prefix_pattern(self.guild)
        await interaction.response.send_message(
            f"The FAQ prefix pattern is set to: ```\n{pattern.pattern}\n```"
        )

    async def set_match_pattern(self, interaction: Interaction, match: str):
        pattern: re.Pattern = await self.store.set_match_pattern(self.guild, match)
        await interaction.response.send_message(
            f"Set the FAQ match pattern to: ```\n{pattern.pattern}\n```"
        )

    async def clear_match_pattern(self, interaction: Interaction):
        await self.store.clear_match_pattern(self.guild)
        await interaction.response.send_message("Cleared the FAQ match pattern")

    async def show_match_pattern(self, interaction: Interaction):
        pattern: re.Pattern = await self.store.require_match_pattern(self.guild)
        await interaction.response.send_message(
            f"The FAQ match pattern is set to: ```\n{pattern.pattern}\n```"
        )


class FaqModal(CogStateModal[FaqGuildState, FaqStore]):
    """
    Base class for all faq modals
    """

    # Delimiter used between alias and tag items
    delim: str = ","

    @classmethod
    def aliases_from_str(cls, aliases_str: str) -> list[str]:
        alias_gen = (alias.strip() for alias in aliases_str.split(cls.delim))
        return [alias for alias in alias_gen if alias]

    @classmethod
    def aliases_to_str(cls, aliases: Iterable[str]) -> str:
        return f"{cls.delim} ".join(aliases)

    @classmethod
    def tags_from_str(cls, tag_str: str) -> list[str]:
        tag_gen = (tag.strip() for tag in tag_str.split(cls.delim))
        return [tag for tag in tag_gen if tag]

    @classmethod
    def tags_to_str(cls, tags: Iterable[str]) -> str:
        return f"{cls.delim} ".join(tags)


class AddFaqModal(FaqModal):
    def __init__(self, interaction: Interaction, state: FaqGuildState):
        super().__init__(
            interaction,
            state,
            title="Add a new FAQ",
            custom_id="commanderbot_ext:faq.add",
        )

        self.key_field = TextInput(
            label="Key",
            style=TextStyle.short,
            placeholder="Ex: sample-text",
            required=True,
        )
        self.aliases_field = TextInput(
            label="Aliases",
            style=TextStyle.short,
            placeholder="A comma separated list of aliases. Ex: foo, bar, baz",
            required=False,
        )
        self.tags_field = TextInput(
            label="Tags (Used for FAQ suggestions)",
            style=TextStyle.short,
            placeholder="A comma separated list of tags. Ex: foo, bar, baz",
            required=False,
        )
        self.content_field = TextInput(
            label="Content",
            style=TextStyle.paragraph,
            placeholder="The content of this FAQ.",
            max_length=constants.MAX_MESSAGE_LENGTH,
            required=True,
        )

        self.add_item(self.key_field)
        self.add_item(self.aliases_field)
        self.add_item(self.tags_field)
        self.add_item(self.content_field)

    async def on_submit(self, interaction: Interaction):
        entry: FaqEntry = await self.store.add_faq(
            guild=self.state.guild,
            key=self.key_field.value.strip(),
            aliases=self.aliases_from_str(self.aliases_field.value),
            tags=self.tags_from_str(self.tags_field.value),
            content=self.content_field.value,
            user_id=interaction.user.id,
        )
        await interaction.response.send_message(f"Added FAQ: `{entry.key}`")


class ModifyFaqModal(FaqModal):
    def __init__(self, interaction: Interaction, state: FaqGuildState, entry: FaqEntry):
        self.faq_key: str = entry.key
        super().__init__(
            interaction,
            state,
            title=f"Modifying FAQ: {self.faq_key}",
            custom_id="commanderbot_ext:faq.modify",
        )

        self.aliases_field = TextInput(
            label="Aliases",
            style=TextStyle.short,
            placeholder="A comma separated list of aliases. Ex: foo, bar, baz",
            default=self.aliases_to_str(entry.sorted_aliases),
            required=False,
        )
        self.tags_field = TextInput(
            label="Tags (Used for FAQ suggestions)",
            style=TextStyle.short,
            placeholder="A comma separated list of tags. Ex: foo, bar, baz",
            default=self.tags_to_str(entry.sorted_tags),
            required=False,
        )
        self.content_field = TextInput(
            label="Content",
            style=TextStyle.paragraph,
            placeholder="The content of this FAQ.",
            default=entry.content,
            max_length=constants.MAX_MESSAGE_LENGTH,
            required=True,
        )

        self.add_item(self.aliases_field)
        self.add_item(self.tags_field)
        self.add_item(self.content_field)

    async def on_submit(self, interaction: Interaction):
        entry: FaqEntry = await self.store.modify_faq(
            guild=self.state.guild,
            key=self.faq_key,
            aliases=self.aliases_from_str(self.aliases_field.value),
            tags=self.tags_from_str(self.tags_field.value),
            content=self.content_field.value,
            user_id=interaction.user.id,
        )
        await interaction.response.send_message(f"Modified FAQ: `{entry.key}`")
