from discord import Interaction, app_commands

import commanderbot.lib.predicates as predicates

__all__ = ("is_owner", "is_administrator", "is_guild_admin_or_bot_owner")


def is_owner():
    def predicate(interaction: Interaction) -> bool:
        return predicates.is_owner(interaction.client, interaction.user)

    return app_commands.check(predicate)


def is_administrator():
    return app_commands.checks.has_permissions(administrator=True)


def is_guild_admin_or_bot_owner():
    def predicate(interaction: Interaction) -> bool:
        # Check if the interaction user is a bot owner
        if predicates.is_owner(interaction.client, interaction.user):
            return True

        # Check if the interaction user is a guild admin
        if interaction.guild and predicates.is_member(interaction.user):
            return interaction.user.guild_permissions.administrator

        return False

    return app_commands.check(predicate)
