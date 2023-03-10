import re
import uuid
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Self

VERSION_PATTERN = re.compile(r"\d+\.\d+\.\d+")


@dataclass(repr=False)
class Version:
    major: int
    minor: int
    patch: int

    @classmethod
    def from_str(cls, version_str: str) -> Optional["Version"]:
        if VERSION_PATTERN.match(version_str):
            version_numbers: list[int] = [int(i) for i in version_str.split(".")][:3]
            return cls(*version_numbers)

    def as_list(self) -> list[int]:
        return [self.major, self.minor, self.patch]

    def __repr__(self) -> str:
        return str(self.as_list())

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"


class ModuleType(Enum):
    DATA = "data"
    RESOURCE = "resources"
    SKIN = "skin_pack"


class Manifest:
    """
    A complete manifest
    """

    def __init__(
        self,
        module_type: ModuleType,
        name: str,
        description: str,
        min_engine_version: Version,
    ):
        self.module_type: ModuleType = module_type
        self.name: str = name
        self.description: str = description
        self.min_engine_version: Version = min_engine_version

        self.pack_uuid: str = str(uuid.uuid4())
        self.module_uuid: str = str(uuid.uuid4())
        self.dependencies: list[str] = []

    def add_dependency(self, other: Self):
        """
        Adds `other` as a dependency to this manifest
        """
        self.dependencies.append(other.pack_uuid)

    def common_name(self) -> str:
        """
        Common name for a manifest with the stored module type
        """
        match self.module_type:
            case ModuleType.DATA:
                return "Behavior Pack"
            case ModuleType.RESOURCE:
                return "Resource Pack"
            case ModuleType.SKIN:
                return "Skin Pack"
            case _:
                return "Unknown Pack"

    def as_dict(self) -> dict:
        """
        Turns manifest contents into a dict
        """
        manifest = {
            "format_version": 2,
            "header": {
                "name": self.name,
                "description": self.description,
                "uuid": self.pack_uuid,
                "version": [1, 0, 0],
                "min_engine_version": self.min_engine_version.as_list(),
            },
            "modules": [
                {
                    "type": self.module_type.value,
                    "uuid": self.module_uuid,
                    "version": [1, 0, 0],
                }
            ],
        }

        if self.dependencies:
            manifest["dependencies"] = [
                {
                    "uuid": dep,
                    "version": [1, 0, 0],
                }
                for dep in self.dependencies
            ]

        return manifest
