import argparse
import json
import os
from logging import getLogger

from dotenv import load_dotenv

from commanderbot.core.commander_bot import CommanderBot
from commanderbot.core.logging import setup_logging

__all__ = ("run",)


def run():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("config", help="Configuration file")
    arg_parser.add_argument(
        "--token",
        help="Bot token (prefer using the BOT_TOKEN environment variable)",
    )
    arg_parser.add_argument(
        "--tokenfile",
        help="Bot token file (prefer using the BOT_TOKEN environment variable)",
    )
    arg_parser.add_argument(
        "--envfile",
        help="The .env file to load environment variables from (defaults to .env)",
        default=".env",
    )
    arg_parser.add_argument(
        "--synctree",
        help="Sync global app commands after the bot has logged in (Useful for setting up the bot for the first time)",
        action="store_true",
    )
    arg_parser.add_argument("--log", help="Log level", default="WARNING")
    parsed_args = arg_parser.parse_args()

    setup_logging(parsed_args.log, detailed=True)

    log = getLogger(__name__)

    log.info("Hello!")

    log.info(f"Log level: {parsed_args.log}")
    log.info(f"Configuration file: {parsed_args.config}")

    log.debug("Parsing configuration file...")

    config = json.load(open(parsed_args.config))

    log.debug("Successfully parsed configuration file!")

    log.info(f"Number of configuration keys: {len(config)}")

    envfile = parsed_args.envfile
    load_dotenv(envfile)

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

    config["sync_tree"] = parsed_args.synctree

    log.warning("Running bot...")

    bot = CommanderBot(**config)

    bot.run(bot_token)

    log.warning("Bot has shut down.")

    log.info("Goodbye!")
