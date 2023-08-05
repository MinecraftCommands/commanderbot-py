from typing import Optional

from discord import Interaction, InteractionMessage, Member, Permissions
from discord.app_commands import (
    Transform,
    Transformer,
    command,
    default_permissions,
    describe,
    guild_only,
)
from discord.app_commands.checks import bot_has_permissions
from discord.app_commands.models import Choice
from discord.enums import AppCommandOptionType
from discord.ext.commands import Bot, Cog
from discord.interactions import Interaction

from commanderbot.ext.moderation.moderation_exceptions import (
    CannotBanBotOrSelf,
    CannotBanElevatedUsers,
    CannotKickBotOrSelf,
    CannotKickElevatedUsers,
)
from commanderbot.lib.allowed_mentions import AllowedMentions

KICK_EMOJI: str = "👢"
BAN_EMOJI: str = "🔨"
MESSAGE_SENT_EMOJI: str = "✉️"
ERROR_EMOJI: str = "🔥"


class DeleteMessageHistoryTransformer(Transformer):
    """
    A transformer for validating that a number representing seconds is between `0` and `604800`

    Also provides autocomplete options that matches the ban UI
    """

    @property
    def type(self) -> AppCommandOptionType:
        return AppCommandOptionType.integer

    @property
    def min_value(self) -> int:
        return 0

    @property
    def max_value(self) -> int:
        return 604800

    async def transform(self, interaction: Interaction, value: int) -> int:
        return value

    async def autocomplete(
        self, interaction: Interaction, value: int
    ) -> list[Choice[int]]:
        return [
            Choice(name="Don't delete any", value=0),
            Choice(name="Previous hour", value=3600),
            Choice(name="Previous 6 hours", value=21600),
            Choice(name="Previous 12 hours", value=43200),
            Choice(name="Previous 24 hours", value=86400),
            Choice(name="Previous 3 days", value=259200),
            Choice(name="Previous 7 days", value=604800),
        ]


class ModerationCog(Cog, name="commanderbot.ext.moderation"):
    def __init__(self, bot: Bot):
        self.bot: Bot = bot

    def _user_is_bot_or_interaction_user(
        self, user: Member, interaction: Interaction
    ) -> bool:
        return user == self.bot.user or user == interaction.user

    def _is_elevated(self, user: Member) -> bool:
        return bool(user.guild_permissions & Permissions.elevated())

    @command(name="kick", description="Kick a user from this server")
    @describe(
        user="The user to kick",
        reason="The reason for the kick (This will also be sent as a DM to the user)",
    )
    @guild_only
    @default_permissions(kick_members=True)
    @bot_has_permissions(kick_members=True)
    async def cmd_kick(
        self, interaction: Interaction, user: Member, reason: Optional[str]
    ):
        # Make sure we aren't trying to kick the bot or the user running the command
        if self._user_is_bot_or_interaction_user(user, interaction):
            raise CannotKickBotOrSelf

        # Make sure we aren't trying to kick users with elevated permissions
        if self._is_elevated(user):
            raise CannotKickElevatedUsers

        # Send the kick response and retrieve it so we can reference it later
        kick_msg: str = f"Kicked {user.mention}"
        kick_reason_msg: str = f"for:\n> {reason}"
        await interaction.response.send_message(
            f"{kick_msg} {kick_reason_msg}" if reason else kick_msg,
            allowed_mentions=AllowedMentions.none(),
        )
        response: InteractionMessage = await interaction.original_response()

        # Attempt to DM if a reason was included
        # We do this before kicking in case this is the only mutual server
        if reason:
            try:
                await user.send(
                    f"{KICK_EMOJI} You were kicked from **{interaction.guild}** for:\n> {reason}",
                )
                await response.add_reaction(MESSAGE_SENT_EMOJI)
            except:
                pass

        # Actually kick the user
        try:
            await user.kick(reason=reason if reason else "None provided")
            await response.add_reaction(KICK_EMOJI)
        except:
            await response.add_reaction(ERROR_EMOJI)

    @command(name="ban", description="Ban a user from this server")
    @describe(
        user="The user to ban",
        reason="The reason for the ban (This will also be sent as a DM to the user)",
        delete_message_history="The amount of message history to delete",
    )
    @guild_only
    @default_permissions(ban_members=True)
    @bot_has_permissions(ban_members=True)
    async def cmd_ban(
        self,
        interaction: Interaction,
        user: Member,
        reason: Optional[str],
        delete_message_history: Optional[
            Transform[int, DeleteMessageHistoryTransformer]
        ],
    ):
        # Make sure we aren't trying to ban the bot or the user running the command
        if self._user_is_bot_or_interaction_user(user, interaction):
            raise CannotBanBotOrSelf

        # Make sure we aren't trying to ban users with elevated permissions
        if self._is_elevated(user):
            raise CannotBanElevatedUsers

        # Send the ban response and retrieve it so we can reference it later
        ban_msg: str = f"Banned {user.mention}"
        ban_reason_msg: str = f"for:\n> {reason}"
        await interaction.response.send_message(
            f"{ban_msg} {ban_reason_msg}" if reason else ban_msg,
            allowed_mentions=AllowedMentions.none(),
        )
        response: InteractionMessage = await interaction.original_response()

        # Attempt to DM if a reason was included
        # We do this before banning in case this is the only mutual server
        if reason:
            try:
                await user.send(
                    f"{BAN_EMOJI} You were banned from **{interaction.guild}** for:\n> {reason}",
                )
                await response.add_reaction(MESSAGE_SENT_EMOJI)
            except:
                pass

        # Actually ban the user
        try:
            await user.ban(
                delete_message_seconds=delete_message_history or 0,
                reason=reason if reason else "None provided",
            )
            await response.add_reaction(BAN_EMOJI)
        except:
            await response.add_reaction(ERROR_EMOJI)
