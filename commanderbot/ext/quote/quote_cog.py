import re
from itertools import chain

from discord import Embed, Interaction, Member, Message, User
from discord.app_commands import (
    Transform,
    allowed_contexts,
    allowed_installs,
    command,
    describe,
)
from discord.ext.commands import Bot, Cog
from discord.utils import format_dt

from commanderbot.ext.quote.quote_exceptions import (
    ChannelNotMessageable,
    MissingQuotePermissions,
)
from commanderbot.lib import (
    AllowedMentions,
    MemberOrUser,
    MessageableGuildChannel,
    is_member,
    is_messagable_guild_channel,
)
from commanderbot.lib.app_commands import MessageTransformer

AUTO_EMBED_PATTERN = re.compile(r"^https?:\/\/\S\S+$")


class QuoteCog(Cog, name="commanderbot.ext.quote"):
    def __init__(self, bot: Bot):
        self.bot: Bot = bot

    def _user_can_quote(
        self, user: MemberOrUser, channel: MessageableGuildChannel
    ) -> bool:
        # Return early if `user` is not a guild member.
        if not is_member(user):
            return False

        # User is a guild member, so check if they can quote this channel.
        quoter_permissions = channel.permissions_for(user)
        can_quote = (
            quoter_permissions.read_messages and quoter_permissions.read_message_history
        )
        return can_quote

    def _is_just_media_link(self, message: Message) -> bool:
        # Check if message is just a media link, which creates a single embed.
        return (
            bool(AUTO_EMBED_PATTERN.match(message.content)) and len(message.embeds) == 1
        )

    def _format_name(self, user: User | Member) -> str:
        if user.display_name.lower() == user.name.lower():
            return user.display_name
        return f"{user.display_name} ({user.name})"

    async def _do_quote(
        self,
        interaction: Interaction,
        message: Message,
        phrasing: str,
        allowed_mentions: AllowedMentions,
    ):
        # Make sure the channel can be quoted from.
        message_channel = message.channel
        if not is_messagable_guild_channel(message_channel):
            raise ChannelNotMessageable

        # Make sure the quoter has read permissions in the channel.
        quoter: MemberOrUser = interaction.user
        if not self._user_can_quote(quoter, message_channel):
            raise MissingQuotePermissions

        # Build the message content containing the quote metadata.
        quote_ts: str = format_dt(message.created_at, style="R")
        if message.edited_at:
            quote_ts += f" (edited {format_dt(message.edited_at, style='R')})"

        content: str = (
            f"{phrasing} {message.author.mention} from {quote_ts} → {message.jump_url}"
        )

        # Send the quote response. The embed will be omitted if there's no message content
        # or the message content is just a media link that creates a single embed.
        if not message.content or self._is_just_media_link(message):
            await interaction.response.send_message(
                content, allowed_mentions=allowed_mentions
            )
        else:
            quote_embed = Embed(
                description=message.content,
            )
            quote_embed.set_author(
                name=self._format_name(message.author),
                icon_url=message.author.display_avatar.url,
            )
            await interaction.response.send_message(
                content, embed=quote_embed, allowed_mentions=allowed_mentions
            )

        # Account for any attachments/embeds on the original message. We have to send
        # these separately from the quote embed, because the quote embed takes
        # precedence and will stop other attachments/embeds from appearing.
        attachment_urls_gen = (att.url for att in message.attachments)
        embed_urls_gen = (embed.url for embed in message.embeds if embed.url)

        assert is_messagable_guild_channel(interaction.channel)
        for url in chain(attachment_urls_gen, embed_urls_gen):
            await interaction.channel.send(url)

    @command(name="quote", description="Quote a message")
    @describe(message_link="A message link to quote")
    @allowed_installs(guilds=True)
    @allowed_contexts(guilds=True)
    async def cmd_quote(
        self,
        interaction: Interaction,
        message_link: Transform[Message, MessageTransformer],
    ):
        await self._do_quote(
            interaction,
            message_link,
            phrasing="Quoted",
            allowed_mentions=AllowedMentions.none(),
        )

    @command(name="quotem", description="Quote a message and mention the author")
    @describe(message_link="A message link to quote")
    @allowed_installs(guilds=True)
    @allowed_contexts(guilds=True)
    async def cmd_quotem(
        self,
        interaction: Interaction,
        message_link: Transform[Message, MessageTransformer],
    ):
        await self._do_quote(
            interaction,
            message_link,
            phrasing="Quote-mentioned",
            allowed_mentions=AllowedMentions.only_users(),
        )
