from dataclasses import dataclass
from typing import Any, Optional, Self

from commanderbot.lib import FromDataMixin


@dataclass
class MCCQManagerOptions(FromDataMixin):
    """
    Attributes
    -----------
    url
        URL or file URI to Minecraft's generated data.
    version_file
        Path to the file containing nothing but the version of the generated files.
    version_whitelist
        Version whitelist, disabled if empty.
    show_versions
        Versions to render in the output by default. If not specified, defaults to the last whitelist entry.
    version_labels
        Labels to print instead of database keys.
    max_results
        Max lines of results, useful to prevent potential chat spam.
    wiki_url
        URL format to provide a as wiki link. The placeholder `{command}` will be replaced by the base command.
    """

    url: str
    version_file: str
    version_whitelist: list[str]
    show_versions: list[str]
    version_labels: dict[str, str]
    max_results: Optional[int]
    wiki_url: Optional[str]

    @classmethod
    def try_from_data(cls, data: Any) -> Optional[Self]:
        if isinstance(data, dict):
            version_whitelist = data.get("version_whitelist", [])
            last_version = version_whitelist[-1] if version_whitelist else None
            show_versions = data.get(
                "show_versions", [last_version] if last_version else []
            )
            return cls(
                url=data["url"],
                version_file=data.get("version_file", "VERSION.txt"),
                version_whitelist=version_whitelist,
                show_versions=show_versions,
                version_labels=data.get("version_labels", {}),
                max_results=data.get("max_results"),
                wiki_url=data.get("wiki_url"),
            )


@dataclass
class MCCQPresenceOptions(FromDataMixin):
    java_version_file_url: Optional[str]
    bedrock_version_file_url: Optional[str]

    @classmethod
    def try_from_data(cls, data: Any) -> Optional[Self]:
        if isinstance(data, dict):
            return cls(
                java_version_file_url=data.get("java_version_file_url"),
                bedrock_version_file_url=data.get("bedrock_version_file_url"),
            )


@dataclass
class MCCQOptions(FromDataMixin):
    java: Optional[MCCQManagerOptions]
    bedrock: Optional[MCCQManagerOptions]

    # Temporary hack until we make a cog for managing the presence
    bot_presence: Optional[MCCQPresenceOptions]

    @classmethod
    def try_from_data(cls, data: Any) -> Optional[Self]:
        if isinstance(data, dict):
            return cls(
                java=MCCQManagerOptions.from_field_optional(data, "java"),
                bedrock=MCCQManagerOptions.from_field_optional(data, "bedrock"),
                bot_presence=MCCQPresenceOptions.from_field_optional(
                    data, "bot_presence"
                ),
            )
