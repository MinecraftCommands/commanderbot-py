import asyncio
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from discord import (
    AllowedMentions,
    Embed,
    ForumChannel,
    ForumTag,
    Interaction,
    Message,
    PartialEmoji,
    PartialMessage,
    Thread,
)

from commanderbot.core.utils import get_app_command
from commanderbot.ext.help_forum.help_forum_exceptions import (
    UnableToResolveUnregistered,
)
from commanderbot.ext.help_forum.help_forum_store import HelpForum, HelpForumStore
from commanderbot.lib import (
    AllowedMentions,
    ConfirmationResult,
    ForumTagID,
    UserID,
    respond_with_confirmation,
    utils,
)
from commanderbot.lib.cogs import CogGuildState


class ThreadState(Enum):
    UNRESOLVED = "Unresolved"
    RESOLVED = "Resolved"


@dataclass
class HelpForumGuildState(CogGuildState):
    """
    Encapsulates the state and logic of the help forum cog, at the guild level.

    Attributes
    -----------
    store
        The store used to interface with persistent data in a database-agnostic way.
    """

    store: HelpForumStore

    async def _change_thread_state(
        self,
        forum: ForumChannel,
        thread: Thread,
        forum_data: HelpForum,
        state: ThreadState,
    ):
        # Require the tags to exist
        unresolved_tag_id: ForumTagID = forum_data.unresolved_tag_id
        resolved_tag_id: ForumTagID = forum_data.resolved_tag_id

        valid_unresolved_tag: ForumTag = utils.require_forum_tag_id(
            forum, unresolved_tag_id
        )
        valid_resolved_tag: ForumTag = utils.require_forum_tag_id(
            forum, resolved_tag_id
        )

        # Create a new tag list from the first 4 tags that aren't a state tag
        tags: list[ForumTag] = []

        applied_tags_gen = (
            t
            for t in sorted(thread.applied_tags, key=lambda x: x.id)
            if t.id not in forum_data.thread_state_tags
        )
        for tag in applied_tags_gen:
            if len(tags) == 4:
                break
            tags.append(tag)

        # Add the new state tag
        match state:
            case ThreadState.UNRESOLVED:
                tags = [*tags, valid_unresolved_tag]
            case ThreadState.RESOLVED:
                tags = [valid_resolved_tag, *tags]

        # Edit thread to change tags and state
        await thread.edit(
            applied_tags=tags,
            archived=(state == ThreadState.RESOLVED),
            reason=f"{state.value} the thread",
        )

    async def _get_help_forum(self, forum: ForumChannel) -> Optional[HelpForum]:
        return await self.store.get_help_forum(self.guild, forum)

    async def on_thread_create(self, forum: ForumChannel, thread: Thread):
        """
        Whenever a thread is created, pin the first message and set the state to unresolved
        """

        # Get help forum data
        forum_data = await self._get_help_forum(forum)
        if not forum_data:
            return

        # Ignore newly created threads if it has the resolved tag
        # This is a QoL feature for server moderators so they can create threads that will be pinned
        if utils.thread_has_forum_tag_with_id(thread, forum_data.resolved_tag_id):
            return

        # Schedule the thread creation functions
        # Since `_setup_thread` has a longish delay and the rest of the functions don't depend
        # on it, we schedule all all of them instead of sequentially awaiting them
        await utils.async_schedule(
            self._setup_thread(thread, forum_data),
            self._change_thread_state(
                forum, thread, forum_data, ThreadState.UNRESOLVED
            ),
            self.store.increment_threads_created(forum_data),
        )

    async def _setup_thread(self, thread: Thread, forum_data: HelpForum):
        # Delay setup so the thread is hopefully created on Discord's end
        await asyncio.sleep(1.0)

        # Get `/resolve` command mention if it exists
        resolve_cmd: str = "`/resolve`"
        if cmd := get_app_command(self.bot, "resolve"):
            resolve_cmd = cmd.mention

        # Pin the starter message
        try:
            await thread.get_partial_message(thread.id).pin()
        except:
            pass

        # Send a message with an embed that tells users how to resolve their thread
        resolved_emoji: str = forum_data.resolved_emoji
        embed = Embed(
            title="Thanks for asking your question",
            description="\n".join(
                (
                    f"- When your question has been answered, please resolve your post.",
                    f"- You can resolve your post by using {resolve_cmd}, reacting to a message with {resolved_emoji}, or sending {resolved_emoji} as a message.",
                    f"- Once your post has been resolved, any additional messages or reactions will unresolve it.",
                )
            ),
            color=0x00ACED,
        )
        await thread.send(embed=embed)

    async def on_bot_pin_starter_message(
        self, forum: ForumChannel, thread: Thread, message: Message
    ):
        """
        If `forum` is a help forum and `message` is referencing the thread starter
        message, then delete `message`
        """
        # Return early if the forum isn't registered
        if not await self._get_help_forum(forum):
            return

        # Delete the pin message if it's about pinning the starter message
        if (ref := message.reference) and ref.message_id == thread.id:
            await message.delete(delay=0.5)

    async def on_unresolve(self, forum: ForumChannel, thread: Thread):
        """
        If `forum` is a help forum, set the thread state to unresolved
        """

        # Get help forum data
        forum_data = await self._get_help_forum(forum)
        if not forum_data:
            return

        # Change the thread state to 'unresolved'
        await self._change_thread_state(
            forum, thread, forum_data, ThreadState.UNRESOLVED
        )

        # Send unresolved message
        await thread.send(
            f"{forum_data.partial_unresolved_emoji} This post has been unresolved"
        )

    async def on_resolve_message(
        self, forum: ForumChannel, thread: Thread, message: Message
    ):
        """
        If `forum` is a help forum, set the thread state to resolved if `message` contains just the resolved emoji
        """

        # Get help forum data
        forum_data = await self._get_help_forum(forum)
        if not forum_data:
            return

        # Return early if the emoji isn't the resolved emoji
        emoji = PartialEmoji.from_str(message.content)
        if emoji != forum_data.partial_resolved_emoji:
            return

        # Send resolved message
        await thread.send(
            "\n".join(
                (
                    f"{forum_data.partial_resolved_emoji} {message.author.mention} resolved this post",
                    f"-# Any additional messages or reactions will unresolve this post",
                )
            ),
            allowed_mentions=AllowedMentions.none(),
        )

        # Change the thread state to 'resolved'
        await self._change_thread_state(forum, thread, forum_data, ThreadState.RESOLVED)

        # Increment resolutions
        await self.store.increment_resolutions(forum_data)

    async def on_resolve_reaction(
        self,
        forum: ForumChannel,
        thread: Thread,
        message: PartialMessage,
        emoji: PartialEmoji,
        user_id: UserID,
    ):
        """
        If `forum` is a help forum, set the thread state to resolved if `emoji` is the resolved emoji
        """

        # Get help forum data
        forum_data = await self._get_help_forum(forum)
        if not forum_data:
            return

        # Return early if the emoji isn't the resolved emoji
        if emoji != forum_data.partial_resolved_emoji:
            return

        # React to message with resolved emoji
        await message.add_reaction(forum_data.partial_resolved_emoji)

        # Send resolved message
        await message.reply(
            "\n".join(
                (
                    f"{forum_data.partial_resolved_emoji} <@{user_id}> resolved this post",
                    f"-# Any additional messages or reactions will unresolve this post",
                )
            ),
            mention_author=False,
            allowed_mentions=AllowedMentions.none(),
        )

        # Change the thread state to 'resolved'
        await self._change_thread_state(forum, thread, forum_data, ThreadState.RESOLVED)

        # Increment resolutions
        await self.store.increment_resolutions(forum_data)

    async def on_resolve_command(
        self, interaction: Interaction, forum: ForumChannel, thread: Thread
    ):
        """
        If `forum` is a help forum, set the thread state to resolved when `/resolve` is ran in `thread`
        """

        # Get help forum data
        forum_data = await self._get_help_forum(forum)
        if not forum_data:
            raise UnableToResolveUnregistered(forum.id)

        # Send resolved message
        await interaction.response.send_message(
            "\n".join(
                (
                    f"{forum_data.partial_resolved_emoji} {interaction.user.mention} resolved this post",
                    f"-# Any additional messages or reactions will unresolve this post",
                )
            ),
            allowed_mentions=AllowedMentions.none(),
        )

        # Change the thread state to 'resolved'
        await self._change_thread_state(forum, thread, forum_data, ThreadState.RESOLVED)

        # Increment resolutions
        await self.store.increment_resolutions(forum_data)

    async def register_forum_channel(
        self,
        interaction: Interaction,
        forum: ForumChannel,
        unresolved_emoji: str,
        resolved_emoji: str,
        unresolved_tag: str,
        resolved_tag: str,
    ):
        forum_data = await self.store.register_forum_channel(
            self.guild,
            forum,
            unresolved_emoji,
            resolved_emoji,
            unresolved_tag,
            resolved_tag,
        )
        await interaction.response.send_message(
            f"Registered <#{forum_data.channel_id}> as a help forum"
        )

    async def deregister_forum_channel(
        self,
        interaction: Interaction,
        forum: ForumChannel,
    ):
        # Try to get the forum channel
        forum_data = await self.store.require_help_forum(self.guild, forum)

        # Respond to this interaction with a confirmation dialog
        result: ConfirmationResult = await respond_with_confirmation(
            interaction,
            f"Are you sure you want to deregister <#{forum_data.channel_id}>?",
            timeout=10,
        )

        match result:
            case ConfirmationResult.YES:
                # If the answer was yes, attempt to deregister the forum channel and send a response
                try:
                    await self.store.deregister_forum_channel(self.guild, forum)
                    await interaction.followup.send(
                        content=f"Deregistered <#{forum_data.channel_id}> from being a help forum"
                    )
                except Exception as ex:
                    await interaction.delete_original_response()
                    raise ex
            case _:
                # If the answer was no, send a response
                await interaction.followup.send(
                    f"Did not deregister <#{forum_data.channel_id}> from being a help forum"
                )

    async def details(self, interaction: Interaction, forum: ForumChannel):
        # Get data from the help forum if it was registered
        forum_data = await self.store.require_help_forum(self.guild, forum)
        unresolved_tag = forum.get_tag(forum_data.unresolved_tag_id)
        resolved_tag = forum.get_tag(forum_data.resolved_tag_id)

        formatted_unresolved_tag = (
            f"{utils.format_forum_tag(unresolved_tag)}"
            if unresolved_tag
            else "**No tag set!**"
        )
        formatted_resolved_tag = (
            f"{utils.format_forum_tag(resolved_tag)}"
            if resolved_tag
            else "**No tag set!**"
        )

        # Create embed fields
        fields: dict = {
            "Unresolved Emoji": forum_data.unresolved_emoji,
            "Resolved Emoji": forum_data.resolved_emoji,
            "Unresolved Tag": formatted_unresolved_tag,
            "Resolved Tag": formatted_resolved_tag,
            "Posts": f"`{forum_data.threads_created}`",
            "Resolutions": f"`{forum_data.resolutions}`",
            "Ratio": f"`{':'.join(map(str, forum_data.ratio))}`",
        }

        # Create embed and add fields
        embed: Embed = Embed(title=forum.mention, color=0x00ACED)
        for k, v in fields.items():
            embed.add_field(name=k, value=v)

        await interaction.response.send_message(embed=embed)

    async def modify_unresolved_emoji(
        self, interaction: Interaction, forum: ForumChannel, emoji: str
    ):
        forum_data = await self.store.modify_unresolved_emoji(self.guild, forum, emoji)
        await interaction.response.send_message(
            f"Changed the unresolved emoji for <#{forum_data.channel_id}> to {forum_data.unresolved_emoji}"
        )

    async def modify_resolved_emoji(
        self, interaction: Interaction, forum: ForumChannel, emoji: str
    ):
        forum_data = await self.store.modify_resolved_emoji(self.guild, forum, emoji)
        await interaction.response.send_message(
            f"Changed the resolved emoji for <#{forum_data.channel_id}> to {forum_data.resolved_emoji}"
        )

    async def modify_unresolved_tag(
        self, interaction: Interaction, forum: ForumChannel, tag: str
    ):
        forum_data, new_tag = await self.store.modify_unresolved_tag(
            self.guild, forum, tag
        )
        await interaction.response.send_message(
            f"Changed unresolved tag for <#{forum_data.channel_id}> to {utils.format_forum_tag(new_tag)}"
        )

    async def modify_resolved_tag(
        self, interaction: Interaction, forum: ForumChannel, tag: str
    ):
        forum_data, new_tag = await self.store.modify_resolved_tag(
            self.guild, forum, tag
        )
        await interaction.response.send_message(
            f"Changed resolved tag for <#{forum_data.channel_id}> to {utils.format_forum_tag(new_tag)}"
        )
