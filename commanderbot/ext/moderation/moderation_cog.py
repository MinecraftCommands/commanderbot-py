from typing import Optional

from discord import Interaction, Member, Permissions
from discord.app_commands import (
    ContextMenu,
    allowed_contexts,
    allowed_installs,
    choices,
    command,
    default_permissions,
    describe,
)
from discord.app_commands.checks import bot_has_permissions
from discord.app_commands.models import Choice
from discord.ext.commands import Bot, Cog
from discord.interactions import Interaction

from commanderbot.ext.moderation.moderation_exceptions import (
    CannotBanBotOrSelf,
    CannotBanElevatedUsers,
    CannotKickBotOrSelf,
    CannotKickElevatedUsers,
)
from commanderbot.ext.moderation.moderation_views import ModerationResponse
from commanderbot.lib import AllowedMentions

KICK_COMPROMISED_REASON = "Your account is compromised and is sending scam messages. Feel free to rejoin once you've changed your password."


class ModerationCog(Cog, name="commanderbot.ext.moderation"):
    def __init__(self, bot: Bot):
        self.bot: Bot = bot

        # Create context menu command
        self.ctx_cmd_kick_compromised = ContextMenu(
            name="Kick compromised account", callback=self.cmd_kick_compromised
        )

    async def cog_load(self):
        self.bot.tree.add_command(self.ctx_cmd_kick_compromised)

    async def cog_unload(self):
        self.bot.tree.remove_command(
            self.ctx_cmd_kick_compromised.name, type=self.ctx_cmd_kick_compromised.type
        )

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
    @allowed_installs(guilds=True)
    @allowed_contexts(guilds=True)
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

        # Send the kick response to the channel
        kick_response_view = ModerationResponse(f"👢 Kicked {user.mention}", reason)
        await interaction.response.send_message(
            view=kick_response_view, allowed_mentions=AllowedMentions.none()
        )

        # Attempt to DM if a reason was included
        # We do this before kicking in case this is the only mutual server
        if reason:
            try:
                guild_name: str = interaction.guild.name  # type: ignore
                kick_dm_view = ModerationResponse(
                    f"👢 You were kicked from `{guild_name}`", reason
                )

                await user.send(
                    view=kick_dm_view, allowed_mentions=AllowedMentions.none()
                )
            except:
                pass

        # Actually kick the user
        await user.kick(reason=reason or "No reason given")

    @command(name="ban", description="Ban a user from this server")
    @describe(
        user="The user to ban",
        reason="The reason for the ban (This will also be sent as a DM to the user)",
        delete_message_history="The amount of message history to delete",
    )
    @choices(
        delete_message_history=[
            Choice(name="Don't delete any", value=0),
            Choice(name="Previous hour", value=3600),
            Choice(name="Previous 6 hours", value=21600),
            Choice(name="Previous 12 hours", value=43200),
            Choice(name="Previous 24 hours", value=86400),
            Choice(name="Previous 3 days", value=259200),
            Choice(name="Previous 7 days", value=604800),
        ]
    )
    @allowed_installs(guilds=True)
    @allowed_contexts(guilds=True)
    @default_permissions(ban_members=True)
    @bot_has_permissions(ban_members=True)
    async def cmd_ban(
        self,
        interaction: Interaction,
        user: Member,
        reason: Optional[str],
        delete_message_history: Optional[int],
    ):
        # Make sure we aren't trying to ban the bot or the user running the command
        if self._user_is_bot_or_interaction_user(user, interaction):
            raise CannotBanBotOrSelf

        # Make sure we aren't trying to ban users with elevated permissions
        if self._is_elevated(user):
            raise CannotBanElevatedUsers

        # Send the ban response to the channel
        ban_response_view = ModerationResponse(f"🔨 Banned {user.mention}", reason)
        await interaction.response.send_message(
            view=ban_response_view, allowed_mentions=AllowedMentions.none()
        )

        # Attempt to DM if a reason was included
        # We do this before banning in case this is the only mutual server
        if reason:
            try:
                guild_name: str = interaction.guild.name  # type: ignore
                ban_dm_view = ModerationResponse(
                    f"🔨 You were banned from `{guild_name}`", reason
                )
                await user.send(
                    view=ban_dm_view, allowed_mentions=AllowedMentions.none()
                )
            except:
                pass

        # Actually ban the user
        await user.ban(
            delete_message_seconds=delete_message_history or 0,
            reason=reason or "No reason given",
        )

    @allowed_installs(guilds=True)
    @allowed_contexts(guilds=True)
    @default_permissions(ban_members=True)
    @bot_has_permissions(ban_members=True)
    async def cmd_kick_compromised(self, interaction: Interaction, user: Member):
        # Make sure we aren't trying to kick the bot or the user running the command
        if self._user_is_bot_or_interaction_user(user, interaction):
            raise CannotKickBotOrSelf

        # Make sure we aren't trying to kick users with elevated permissions
        if self._is_elevated(user):
            raise CannotKickElevatedUsers

        # Send the response to the channel
        response_view = ModerationResponse(
            f"👢 Kicked {user.mention}", KICK_COMPROMISED_REASON
        )
        await interaction.response.send_message(
            view=response_view, allowed_mentions=AllowedMentions.none()
        )

        # Attempt to DM
        # We do this before banning in case this is the only mutual server
        try:
            guild_name: str = interaction.guild.name  # type: ignore
            dm_view = ModerationResponse(
                f"👢 You were kicked from `{guild_name}`", KICK_COMPROMISED_REASON
            )
            await user.send(view=dm_view, allowed_mentions=AllowedMentions.none())
        except:
            pass

        # Ban the user and delete any messages they sent in the last hour
        await user.ban(delete_message_seconds=3600)

        # Unban the user
        await user.unban()
