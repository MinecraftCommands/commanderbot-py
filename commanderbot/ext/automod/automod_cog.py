import json
from datetime import datetime
from typing import Optional

from discord import (
    Attachment,
    AutoModAction,
    AutoModRuleActionType,
    Guild,
    Interaction,
    Member,
    Message,
    Reaction,
    Thread,
    ThreadMember,
    User,
)
from discord.abc import Messageable
from discord.app_commands import (
    Group,
    allowed_contexts,
    allowed_installs,
    command,
    default_permissions,
    describe,
)
from discord.ext.commands import Bot, Cog, GroupCog

from commanderbot.ext.automod.automod_data import AutomodData
from commanderbot.ext.automod.automod_guild_state import AutomodGuildState
from commanderbot.ext.automod.automod_options import AutomodOptions
from commanderbot.ext.automod.automod_state import AutomodState
from commanderbot.ext.automod.automod_store import AutomodStore
from commanderbot.ext.automod.rule.rule import AutomodRule
from commanderbot.lib import is_guild
from commanderbot.lib.cogs import CogGuildStateManager
from commanderbot.lib.databases.json_db import JsonDB
from commanderbot.lib.predicates import (
    is_bot,
    is_guild_channel,
    is_member,
    is_messagable_guild_channel,
    is_thread,
)
from commanderbot.lib.types import GuildChannel
from commanderbot.lib.utils import str_to_file


@allowed_installs(guilds=True)
@allowed_contexts(guilds=True)
@default_permissions(administrator=True)
class AutomodCog(
    GroupCog,
    name="commanderbot.ext.automod",
    group_name="automod",
    description="Automate a variety of moderation tasks",
):
    def __init__(self, bot: Bot, **options):
        self.bot: Bot = bot
        self.options = AutomodOptions.model_validate(options)
        self.store = AutomodStore(
            bot=self.bot, cog=self, db=JsonDB(self.options.database, AutomodData)
        )
        self.state = AutomodState(
            bot=self.bot,
            cog=self,
            guilds=CogGuildStateManager(
                bot=self.bot,
                cog=self,
                factory=lambda guild: AutomodGuildState(
                    bot=self.bot, cog=self, guild=guild, store=self.store
                ),
            ),
            store=self.store,
        )

    # @@ COMMANDS

    # @@ automod schema
    @command(name="schema", description="Export the Json schema for automod rules")
    async def cmd_automod_schema(self, interaction: Interaction):
        schema = json.dumps(AutomodRule.model_json_schema())
        file = str_to_file(schema, "schema.json")
        await interaction.response.send_message(
            "Exported Json schema for automod rules", file=file, ephemeral=True
        )

    # @@ automod log
    cmd_automod_log = Group(name="log", description="Configure the default log channel")

    # @@ automod log set

    # @@ automod log modify

    # @@ automod log remove

    # @@ automod log details

    # @@ automod rules
    cmd_automod_rules = Group(name="rules", description="Manage automod rules")

    # @@ automod rules add
    @cmd_automod_rules.command(name="add", description="Add a new automod rule")
    async def cmd_automod_rules_all(self, interaction: Interaction):
        assert is_guild(interaction.guild)
        await self.state[interaction.guild].add_rule(interaction)

    # @@ automod rules modify
    @cmd_automod_rules.command(name="modify", description="Modify an automod rule")
    @describe(rule="The automod rule to modify")
    async def cmd_automod_rules_modify(self, interaction: Interaction, rule: str):
        assert is_guild(interaction.guild)
        await self.state[interaction.guild].modify_rule(interaction, rule)

    # @@ automod rules upload
    @cmd_automod_rules.command(name="upload", description="Upload an automod rule")
    @describe(
        file="A Json file containing an automod rule (If the rule already exists, it will be modified)"
    )
    async def cmd_automod_rules_upload(
        self, interaction: Interaction, file: Attachment
    ):
        assert is_guild(interaction.guild)
        await self.state[interaction.guild].upload_rule(interaction, file)

    # @@ automod rules remove
    @cmd_automod_rules.command(name="remove", description="Remove an automod rule")
    @describe(rule="The automod rule to remove")
    async def cmd_automod_rules_remove(self, interaction: Interaction, rule: str):
        assert is_guild(interaction.guild)
        await self.state[interaction.guild].remove_rule(interaction, rule)

    # @@ automod rules details
    @cmd_automod_rules.command(
        name="details", description="Show the details about an automod rule"
    )
    @describe(rule="The automod rule to show details about")
    async def cmd_automod_rules_details(self, interaction: Interaction, rule: str):
        assert is_guild(interaction.guild)
        await self.state[interaction.guild].show_rule_details(interaction, rule)

    # @@ automod rules list
    @cmd_automod_rules.command(name="list", description="List all automod rules")
    async def cmd_automod_rules_list(self, interaction: Interaction):
        assert is_guild(interaction.guild)
        await self.state[interaction.guild].list_rules(interaction)

    # @@ automod rules enable
    @cmd_automod_rules.command(name="enable", description="Enable an automod rule")
    @describe(rule="The automod rule to enable")
    async def cmd_automod_rules_enable(self, interaction: Interaction, rule: str):
        assert is_guild(interaction.guild)
        await self.state[interaction.guild].enable_rule(interaction, rule)

    # @@ automod rules disable
    @cmd_automod_rules.command(name="disable", description="disable an automod rule")
    @describe(rule="The automod rule to disable")
    async def cmd_automod_rules_disable(self, interaction: Interaction, rule: str):
        assert is_guild(interaction.guild)
        await self.state[interaction.guild].disable_rule(interaction, rule)

    # @@ automod rules enable-all
    @cmd_automod_rules.command(
        name="enable-all", description="Enable all automod rules"
    )
    async def cmd_automod_rules_enable_all(self, interaction: Interaction):
        assert is_guild(interaction.guild)
        await self.state[interaction.guild].enable_all_rule(interaction)

    # @@ automod rules disable-all
    @cmd_automod_rules.command(
        name="disable-all", description="Disable all automod rules"
    )
    async def cmd_automod_rules_disable_all(self, interaction: Interaction):
        assert is_guild(interaction.guild)
        await self.state[interaction.guild].disable_all_rule(interaction)

    # @@ automod buckets
    cmd_automod_buckets = Group(name="buckets", description="Manage automod buckets")

    # @@ automod buckets add

    # @@ automod buckets modify

    # @@ automod buckets remove

    # @@ automod buckets details

    # @@ automod buckets list

    # @@ automod buckets clear

    # @@ automod buckets enable

    # @@ automod buckets disable

    # @@ automod buckets clear-all

    # @@ automod buckets enable-all

    # @@ automod buckets disable-all

    # @@ LISTENERS

    # @@ DISCORD AUTOMOD

    @Cog.listener()
    async def on_automod_action(self, execution: AutoModAction):
        guild_state = self.state[execution.guild]
        match execution.action.type:
            case AutoModRuleActionType.block_message:
                await guild_state.on_discord_automod_action_block_message(execution)
            case AutoModRuleActionType.timeout:
                await guild_state.on_discord_automod_action_timeout(execution)
            case AutoModRuleActionType.block_member_interactions:
                await guild_state.on_discord_automod_action_block_member_interactions(
                    execution
                )

    # @@ CHANNELS

    @Cog.listener()
    async def on_guild_channel_delete(self, channel: GuildChannel):
        """
        https://discordpy.readthedocs.io/en/latest/api.html#discord.on_guild_channel_delete
        """

        if is_guild_channel(channel):
            await self.state[channel.guild].on_guild_channel_deleted(channel)

    @Cog.listener()
    async def on_guild_channel_create(self, channel: GuildChannel):
        """
        https://discordpy.readthedocs.io/en/latest/api.html#discord.on_guild_channel_create
        """

        if is_guild_channel(channel):
            await self.state[channel.guild].on_guild_channel_created(channel)

    @Cog.listener()
    async def on_guild_channel_update(self, before: GuildChannel, after: GuildChannel):
        """
        https://discordpy.readthedocs.io/en/latest/api.html#discord.on_guild_channel_update
        """

        if is_guild_channel(before) and is_guild_channel(after):
            await self.state[after.guild].on_guild_channel_updated(before, after)

    @Cog.listener()
    async def on_guild_channel_pins_update(
        self, channel: GuildChannel | Thread, last_pin: Optional[datetime]
    ):
        """
        https://discordpy.readthedocs.io/en/latest/api.html#discord.on_guild_channel_pins_update
        """

        if is_messagable_guild_channel(channel) or is_thread(channel):
            await self.state[channel.guild].on_guild_channel_pins_updated(
                channel, last_pin
            )

    @Cog.listener()
    async def on_typing(self, channel: Messageable, user: User, when: datetime):
        """
        https://discordpy.readthedocs.io/en/latest/api.html#discord.on_typing
        """

        if is_bot(self.bot, user):
            return

        if not is_member(user):
            return

        if not (is_messagable_guild_channel(channel) or is_thread(channel)):
            return

        await self.state[channel.guild].on_member_typing(channel, user, when)

    # @@ MEMBERS

    def _guild_state_for_member(self, member: Member) -> Optional[AutomodGuildState]:
        if not is_bot(self.bot, member):
            return self.state[member.guild]

    @Cog.listener()
    async def on_member_join(self, member: Member):
        """
        https://discordpy.readthedocs.io/en/latest/api.html#discord.on_member_join
        """

        if guild_state := self._guild_state_for_member(member):
            await guild_state.on_member_joined(member)

    @Cog.listener()
    async def on_member_remove(self, member: Member):
        """
        https://discordpy.readthedocs.io/en/latest/api.html#discord.on_member_remove
        """

        if guild_state := self._guild_state_for_member(member):
            await guild_state.on_member_left(member)

    @Cog.listener()
    async def on_member_update(self, before: Member, after: Member):
        """
        https://discordpy.readthedocs.io/en/latest/api.html#discord.on_member_update
        """

        if guild_state := self._guild_state_for_member(after):
            await guild_state.on_member_updated(before, after)

    @Cog.listener()
    async def on_user_update(self, before: User, after: User):
        """
        https://discordpy.readthedocs.io/en/latest/api.html#discord.on_user_update
        """

        # Go through every guild we can see, and check if the user is a member there
        # For every guild the user is a member of, run the event handler
        for guild in self.bot.guilds:
            if member := guild.get_member(after.id):
                if guild_state := self._guild_state_for_member(member):
                    await guild_state.on_user_updated(before, after)

    @Cog.listener()
    async def on_member_ban(self, guild: Guild, user: User):
        """
        https://discordpy.readthedocs.io/en/latest/api.html#discord.on_member_ban
        """

        await self.state[guild].on_user_banned(user)

    @Cog.listener()
    async def on_member_unban(self, guild: Guild, user: User):
        """
        https://discordpy.readthedocs.io/en/latest/api.html#discord.on_member_unban
        """

        await self.state[guild].on_user_unbanned(user)

    # @@ MESSAGES

    @Cog.listener()
    async def on_message(self, message: Message):
        """
        https://discordpy.readthedocs.io/en/latest/api.html#discord.on_message
        """

        if is_bot(self.bot, message.author):
            return

        if not is_member(message.author):
            return

        channel = message.channel
        if not (is_messagable_guild_channel(channel) or is_thread(channel)):
            return

        await self.state[channel.guild].on_message_sent(message)

    @Cog.listener()
    async def on_message_edit(self, before: Message, after: Message):
        """
        https://discordpy.readthedocs.io/en/latest/api.html#discord.on_message_edit
        """

        if is_bot(self.bot, after.author):
            return

        if not is_member(after.author):
            return

        channel = after.channel
        if not (is_messagable_guild_channel(channel) or is_thread(channel)):
            return

        await self.state[channel.guild].on_message_edited(before, after)

    @Cog.listener()
    async def on_message_delete(self, message: Message):
        """
        https://discordpy.readthedocs.io/en/latest/api.html#discord.on_message_delete
        """

        if is_bot(self.bot, message.author):
            return

        channel = message.channel
        if not (is_messagable_guild_channel(channel) or is_thread(channel)):
            return

        await self.state[channel.guild].on_message_deleted(message)

    # @@ REACTIONS

    @Cog.listener()
    async def on_reaction_add(self, reaction: Reaction, user: User | Member):
        """
        https://discordpy.readthedocs.io/en/latest/api.html#discord.on_reaction_add
        """

        if is_bot(self.bot, user):
            return

        if not is_member(user):
            return

        channel = reaction.message.channel
        if not (is_messagable_guild_channel(channel) or is_thread(channel)):
            return

        await self.state[channel.guild].on_reaction_added(reaction, user)

    @Cog.listener()
    async def on_reaction_remove(self, reaction: Reaction, user: User | Member):
        """
        https://discordpy.readthedocs.io/en/latest/api.html#discord.on_reaction_remove
        """

        if is_bot(self.bot, user):
            return

        if not is_member(user):
            return

        channel = reaction.message.channel
        if not (is_messagable_guild_channel(channel) or is_thread(channel)):
            return

        await self.state[channel.guild].on_reaction_removed(reaction, user)

    # @@ THREADS

    def _guild_state_for_thread(self, thread: Thread) -> Optional[AutomodGuildState]:
        if (parent := thread.parent) and (guild := parent.guild):
            return self.state[guild]

    def _guild_state_for_thread_member(
        self, member: ThreadMember
    ) -> Optional[AutomodGuildState]:
        return self._guild_state_for_thread(member.thread)

    @Cog.listener()
    async def on_thread_create(self, thread: Thread):
        """
        https://discordpy.readthedocs.io/en/latest/api.html#discord.on_thread_create
        """

        if guild_state := self._guild_state_for_thread(thread):
            await guild_state.on_thread_created(thread)

    @Cog.listener()
    async def on_thread_join(self, thread: Thread):
        """
        https://discordpy.readthedocs.io/en/latest/api.html#discord.on_thread_join
        """
        if guild_state := self._guild_state_for_thread(thread):
            await guild_state.on_thread_joined(thread)

    @Cog.listener()
    async def on_thread_update(self, before: Thread, after: Thread):
        """
        https://discordpy.readthedocs.io/en/latest/api.html#discord.on_thread_update
        """

        if guild_state := self._guild_state_for_thread(after):
            await guild_state.on_thread_updated(before, after)

    @Cog.listener()
    async def on_thread_remove(self, thread: Thread):
        """
        https://discordpy.readthedocs.io/en/latest/api.html#discord.on_thread_remove
        """

        if guild_state := self._guild_state_for_thread(thread):
            await guild_state.on_thread_removed(thread)

    @Cog.listener()
    async def on_thread_delete(self, thread: Thread):
        """
        https://discordpy.readthedocs.io/en/latest/api.html#discord.on_thread_delete
        """

        if guild_state := self._guild_state_for_thread(thread):
            await guild_state.on_thread_deleted(thread)

    @Cog.listener()
    async def on_thread_member_join(self, member: ThreadMember):
        """
        https://discordpy.readthedocs.io/en/latest/api.html#discord.on_thread_member_join
        """

        if guild_state := self._guild_state_for_thread_member(member):
            await guild_state.on_thread_member_joined(member)

    @Cog.listener()
    async def on_thread_member_leave(self, member: ThreadMember):
        """
        https://discordpy.readthedocs.io/en/latest/api.html#discord.on_thread_member_leave
        """

        if guild_state := self._guild_state_for_thread_member(member):
            await guild_state.on_thread_member_left(member)
