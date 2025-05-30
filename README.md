# commanderbot-py

A collection of utilities and extensions for discord.py bots.

[![uv-badge]](https://github.com/astral-sh/uv/)
[![package-badge]](https://pypi.python.org/pypi/commanderbot/)
[![version-badge]](https://pypi.python.org/pypi/commanderbot/)

## Requirements

- Python 3.13+
- discord.py 2.5+

## Running your bot

You can run your own bot without writing any code.

You will need the following:

1. Your own [Discord Application](https://discordapp.com/developers/applications) with a bot token.
2. A [configuration file](#configuring-your-bot) for the bot.
3. A Python 3.13+ environment.
   - It is recommended to use a [virtual environment](https://docs.python.org/3/tutorial/venv.html) for this.
   - You can use [pyenv](https://github.com/pyenv/pyenv) to build and run Python 3.13.
4. Run `pip install commanderbot` to install the bot core package.

The first thing you should do is check the CLI help menu:

```bash
python -m commanderbot --help
```

There are several ways to provide a bot token:

1. (Recommended) As the `BOT_TOKEN` environment variable: `BOT_TOKEN=put_your_bot_token_here`
   - Supports `.env` files: use `.env` in the working directory or provide the `--envfile` option
2. As a CLI option: `--token put_your_bot_token_here`
3. As a standalone file: `--tokenfile path_to_file_with_bot_token`
4. Manually, when prompted during start-up

Here's an example that provides the bot token as an argument:

```bash
python -m commanderbot bot.json --token put_your_bot_token_here
```

## Configuring your bot

The current set of configuration options is limited. The following is an example configuration that sets the command prefix, enabled privileged intents, and loads the `sudo`, `status` and `faq` extensions.

> The `sudo` extension is essential to managing the bot. It can do things like syncing commands, setting the bot's profile picture, or even exporting the config.

> An extension prefixed with `$` means the extension is required and cannot be managed while the bot is running. If the extension's config uses the object syntax, you can make the extension required by adding `"required": true`.

> Note that with this configuration, the `faq` extension will require read-write access to `faq.json` in the working directory.

```json
{
  "command_prefix": ".",
  "privileged_intents": {
    "message_content": true,
    "members": true
  },
  "extensions": [
    "$commanderbot.ext.sudo",
    "commanderbot.ext.status",
    {
      "name": "commanderbot.ext.faq",
      "options": {
        "database": "faq.json"
      }
    }
  ]
}
```

[uv-badge]: https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json&style=flat-square
[package-badge]: https://img.shields.io/pypi/v/commanderbot.svg?style=flat-square
[version-badge]: https://img.shields.io/pypi/pyversions/commanderbot.svg?style=flat-square
