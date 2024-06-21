from discord.ext.commands import DefaultHelpCommand


class HelpCommand(DefaultHelpCommand):
    # @overrides DefaultHelpCommand
    def get_ending_note(self) -> str:
        command_name = self.invoked_with
        prefix = self.context.clean_prefix
        return (
            f"Type {prefix}{command_name} <command> for more info on a command.\n"
            f"You can also type {prefix}{command_name} <category> for more info on a category.\n"
            "Don't see the command you want to run? Check out our slash commands instead."
        )
