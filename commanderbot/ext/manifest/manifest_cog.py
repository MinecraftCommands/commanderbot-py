import json
from enum import Enum
from logging import Logger, getLogger
from typing import List, Optional

from discord import Embed, Interaction, Permissions
from discord.app_commands import (
    Choice,
    Group,
    Transform,
    Transformer,
    autocomplete,
    describe,
)
from discord.ext.commands import Bot, Cog

from commanderbot.ext.manifest.manifest_data import Manifest, ModuleType, Version
from commanderbot.ext.manifest.manifest_exceptions import (
    BadResponseFromVersionURL,
    InvalidVersionFormat,
    NoURLInConfig,
    UnableToUpdateLatestVersion,
)
from commanderbot.ext.manifest.manifest_version_manager import ManifestVersionManager
from commanderbot.lib.interactions import checks
from commanderbot.lib.utils import str_to_file

DEFAULT_NAME = "pack.name"
DEFAULT_DESCRIPTION = "pack.description"


class ManifestType(Enum):
    """
    Used for automatically creating an app command transformer
    with autocompletion of these choices
    """

    addon = [ModuleType.DATA, ModuleType.RESOURCE]
    behavior = [ModuleType.DATA]
    resource = [ModuleType.RESOURCE]
    skin = [ModuleType.SKIN]


class VersionTransformer(Transformer):
    """
    A transformer that validates version strings
    """

    async def transform(self, interaction: Interaction, value: str) -> Version:
        if version := Version.from_str(value):
            return version
        raise InvalidVersionFormat


class ManifestCog(Cog, name="commanderbot.ext.manifest"):
    def __init__(self, bot: Bot, **options):
        self.bot: Bot = bot
        self.log: Logger = getLogger(self.qualified_name)

        # Get url option and print a warning if it doesn't exist
        url: Optional[str] = options.get("version_url")
        if not url:
            self.log.warn(
                "No version URL was given in the bot config. "
                f"Using `{ManifestVersionManager.default_version()}` for the latest min engine version"
            )

        # Create and start the manifest version manager
        self.version_manager = ManifestVersionManager(url=url)
        self.version_manager.start()

    def cog_unload(self):
        self.version_manager.stop()

    async def min_engine_version_autocomplete(
        self, interaction: Interaction, value: str
    ) -> List[Choice[str]]:
        """
        An autocomplete callback that alawys returns the latest version
        from the manifest version manager
        """
        latest_version: str = str(self.version_manager.latest_version)
        return [Choice(name=f"latest ({latest_version})", value=latest_version)]

    # @@ COMMANDS

    # Groups
    cmd_manifest = Group(name="manifest", description="Generate a Bedrock manifest")
    cmd_manifests = Group(
        name="manifests",
        description="Manage the manifest generator",
        default_permissions=Permissions(administrator=True),
    )

    # @@ User facing commands

    @cmd_manifest.command(name="generate", description="Generate a Bedrock manifest")
    @describe(
        manifest_type="The type of manifest to generate",
        name="The name of the manifest",
        description="The description for the manifest",
        min_engine_version="The minimum version of Minecraft this manifest is compatible with",
    )
    @autocomplete(min_engine_version=min_engine_version_autocomplete)
    async def cmd_manifest_generate(
        self,
        interaction: Interaction,
        manifest_type: ManifestType,
        name: Optional[str],
        description: Optional[str],
        min_engine_version: Optional[Transform[Version, VersionTransformer]],
    ):
        # Create manifests
        manifest_name = name or DEFAULT_NAME
        manifest_description = description or DEFAULT_DESCRIPTION
        min_version: Version = min_engine_version or self.version_manager.latest_version

        manifests: list[Manifest] = []
        for module_type in manifest_type.value:
            manifests.append(
                Manifest(module_type, manifest_name, manifest_description, min_version)
            )

        # Add resource manifest as a dependency to the behavior manifest if
        # an addon manifest is being generated
        if manifest_type == ManifestType.addon:
            manifests[0].add_dependency(manifests[1])

        # Upload manifest files
        await interaction.response.defer()
        for manifest in manifests:
            manifest_json: str = json.dumps(manifest.as_dict(), indent=4)
            await interaction.followup.send(
                f"**{manifest.common_name()}**",
                file=str_to_file(manifest_json, "manifest.json"),
            )

    # @@ Bot manager commands

    @cmd_manifests.command(
        name="status", description="Shows the status of the manifest generator"
    )
    @checks.is_owner()
    async def cmd_manifests_status(self, interaction: Interaction):
        # Format embed fields
        url: str = self.version_manager.url or "**None set**"

        prev_request_ts: str = "`?`"
        if ts := self.version_manager.prev_request_ts:
            prev_request_ts = f"<t:{ts}:R>"

        next_request_ts: str = "`?`"
        if ts := self.version_manager.next_request_ts:
            next_request_ts = f"<t:{ts}:R>"

        prev_status_code: str = "`?`"
        if status := self.version_manager.prev_status_code:
            prev_status_code = f"`{status}`"

        # Create embed
        embed = Embed(title=f"Status for {self.qualified_name}", color=0x00ACED)
        embed.add_field(name="Version URL", value=url, inline=False)
        embed.add_field(name="Previous request", value=prev_request_ts)
        embed.add_field(name="Next request", value=next_request_ts)
        embed.add_field(name="Previous status code", value=prev_status_code)
        embed.add_field(
            name="Latest min engine version",
            value=f"`{self.version_manager.latest_version}`",
        )

        await interaction.response.send_message(embed=embed)

    @cmd_manifests.command(
        name="update", description="Updates the latest min engine version"
    )
    @checks.is_owner()
    async def cmd_manifests_update(self, interaction: Interaction):
        if not self.version_manager.url:
            raise NoURLInConfig

        # Try to update the latest version
        await self.version_manager.update()
        match self.version_manager.prev_status_code:
            case 200:
                await interaction.response.send_message(
                    f"✅ Updated the latest min engine version to `{self.version_manager.latest_version}`"
                )
            case int() as status_code:
                raise BadResponseFromVersionURL(status_code)
            case _:
                raise UnableToUpdateLatestVersion
