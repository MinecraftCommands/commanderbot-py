import argparse
import os
from logging import Logger, getLogger
from pathlib import Path

from dotenv import load_dotenv

from commanderbot.core.commander_bot import CommanderBot
from commanderbot.core.config import Config
from commanderbot.core.logging import setup_logging

__all__ = ("run",)


def run():
    # Create argument parser and parse arguments
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("config", help="Configuration file", type=Path)
    arg_parser.add_argument(
        "--token",
        help="Bot token (prefer using the BOT_TOKEN environment variable)",
    )
    arg_parser.add_argument(
        "--tokenfile",
        help="Bot token file (prefer using the BOT_TOKEN environment variable)",
        type=Path,
    )
    arg_parser.add_argument(
        "--envfile",
        help="The .env file to load environment variables from (defaults to .env)",
        default=".env",
        type=Path,
    )
    arg_parser.add_argument(
        "--synctree",
        help="Sync global app commands after the bot has logged in (Useful for setting up the bot for the first time)",
        action="store_true",
    )
    arg_parser.add_argument("--log", help="Log level", default="WARNING")
    parsed_args = arg_parser.parse_args()

    # Setup logging and load environment variables
    setup_logging(parsed_args.log, detailed=True)
    load_dotenv(parsed_args.envfile)

    log: Logger = getLogger(__name__)
    log.info("Hello!")
    log.info(f"Log level: {parsed_args.log}")

    # Read config file
    log.info(f"Configuration file: {parsed_args.config}")
    config = Config.from_file(parsed_args.config)  # type: ignore

    # Get bot token
    bot_token = os.environ.get("BOT_TOKEN", None)

    if not bot_token:
        log.warning(
            "Bot token provided in a form other than the BOT_TOKEN environment variable."
        )

        if parsed_args.token:
            log.info("Using bot token provided as an argument.")
            bot_token = parsed_args.token

        elif parsed_args.tokenfile:
            log.info(f"Reading bot token from file: {parsed_args.tokenfile}")
            with open(os.path.abspath(parsed_args.tokenfile)) as fp:
                bot_token = fp.read()

        else:
            bot_token = input("Enter bot token: ")

    log.warning("Running bot...")

    bot = CommanderBot(config, parsed_args.synctree)
    bot.run(bot_token)

    log.warning("Bot has shut down.")

    log.info("Goodbye!")
