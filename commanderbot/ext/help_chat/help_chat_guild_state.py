from dataclasses import dataclass
from datetime import datetime
from typing import Iterable

from discord import CategoryChannel, TextChannel
from discord.ext.commands import Context

from commanderbot.ext.help_chat.help_chat_report import HelpChatReportBuildContext
from commanderbot.ext.help_chat.help_chat_store import HelpChannel, HelpChatStore
from commanderbot.lib import is_category_channel, is_text_channel
from commanderbot.lib.cogs import CogGuildState


@dataclass
class HelpChatGuildState(CogGuildState):
    """
    Encapsulates the state and logic of the help-chat cog, at the guild level.

    Attributes
    -----------
    store
        The store used to interface with persistent data in a database-agnostic way.
    """

    store: HelpChatStore

    @staticmethod
    def _flatten_text_channels(
        channels: tuple[TextChannel | CategoryChannel, ...]
    ) -> Iterable[TextChannel]:
        for channel in channels:
            if is_text_channel(channel):
                yield channel
            elif is_category_channel(channel):
                yield from (ch for ch in channel.channels if is_text_channel(ch))

    async def list_channels(self, ctx: Context):
        if help_channels := await self.store.get_help_channels(self.guild):
            pairs = [
                (help_channel, help_channel.channel(ctx))
                for help_channel in help_channels
            ]
            sorted_pairs = sorted(pairs, key=lambda pair: pair[1].position)
            await ctx.send(
                f"There are {len(sorted_pairs)} help channels:\n"
                + "\n".join(
                    f"{ch.mention} (since {hc.registered_on})"
                    for hc, ch in sorted_pairs
                )
            )
        else:
            await ctx.send(f"No help channels")

    async def list_channels_by_creation_date(self, ctx: Context):
        if help_channels := await self.store.get_help_channels(self.guild):
            channels = [hc.channel(ctx) for hc in help_channels]
            sorted_channels = sorted(channels, key=lambda ch: ch.created_at)
            lines = []
            for ch in sorted_channels:
                ts = int(ch.created_at.timestamp())
                line = f"{ch.mention} <t:{ts}> `{ch.id}`"
                lines.append(line)
            content = "\n".join(lines)
            await ctx.message.reply(content)
        else:
            await ctx.send(f"No help channels")

    async def add_channels(
        self,
        ctx: Context,
        channels: tuple[TextChannel | CategoryChannel, ...],
    ):
        added_help_channels: list[HelpChannel] = []
        already_help_channels: list[HelpChannel] = []
        failed_channels: list[TextChannel] = []

        for channel in self._flatten_text_channels(channels):
            try:
                if already_help_channel := await self.store.get_help_channel(
                    self.guild, channel
                ):
                    already_help_channels.append(already_help_channel)
                else:
                    added_help_channel = await self.store.add_help_channel(
                        self.guild, channel
                    )
                    added_help_channels.append(added_help_channel)
            except:
                self.log.exception("Failed to add help channel")
                failed_channels.append(channel)

        if added_help_channels:
            await ctx.send(
                f"✅ These {len(added_help_channels)} channels are now help channels: "
                + " ".join(ch.channel(ctx).mention for ch in added_help_channels)
            )

        if already_help_channels:
            await ctx.send(
                f"💡 These {len(already_help_channels)} channels were already help channels and "
                + "haven't changed: "
                + " ".join(ch.channel(ctx).mention for ch in already_help_channels)
            )

        if failed_channels:
            await ctx.send(
                f"⚠️ These {len(failed_channels)} channels caused errors:"
                + " ".join(ch.mention for ch in failed_channels)
            )

    async def remove_channels(
        self,
        ctx: Context,
        channels: tuple[TextChannel | CategoryChannel, ...],
    ):
        removed_help_channels: list[TextChannel] = []
        not_help_channels: list[TextChannel] = []
        failed_channels: list[TextChannel] = []

        for channel in self._flatten_text_channels(channels):
            try:
                if await self.store.get_help_channel(self.guild, channel):
                    await self.store.remove_help_channel(self.guild, channel)
                    removed_help_channels.append(channel)
                else:
                    not_help_channels.append(channel)
            except:
                self.log.exception("Failed to remove help channel")
                failed_channels.append(channel)

        if removed_help_channels:
            await ctx.send(
                f"✅ These {len(removed_help_channels)} channels are **no longer** help channels: "
                + " ".join(ch.mention for ch in removed_help_channels)
            )

        if not_help_channels:
            await ctx.send(
                f"💡 These {len(not_help_channels)} channels were **not** already help channels "
                + "and haven't changed: "
                + " ".join(ch.mention for ch in not_help_channels)
            )

        if failed_channels:
            await ctx.send(
                f"⚠️ These {len(failed_channels)} channels caused errors:"
                + " ".join(ch.mention for ch in failed_channels)
            )

    async def build_report(
        self,
        ctx: Context,
        after: datetime,
        before: datetime,
        label: str,
        split_length: int,
        max_rows: int,
        min_score: int,
    ):
        # Build the report, which will send progress updates as each channel is scanned.
        help_channels: list[HelpChannel] = await self.store.get_help_channels(
            self.guild
        )
        report_context = HelpChatReportBuildContext(
            ctx,
            help_channels=help_channels,
            after=after,
            before=before,
            label=label,
        )
        report = await report_context.build()
        # Summarize the report in the current channel, using guild default options.
        await report.summarize(
            ctx,
            split_length=split_length,
            max_rows=max_rows,
            min_score=min_score,
        )
