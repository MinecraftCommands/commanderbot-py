from collections import defaultdict
from dataclasses import dataclass
from typing import Optional, Union

from commanderbot.ext.mcdoc.mcdoc_exceptions import QueryReturnedNoResults
from commanderbot.ext.mcdoc.mcdoc_types import McdocContext, McdocType, deserialize_mcdoc


@dataclass
class SymbolResult:
    identifier: str
    typeDef: McdocType

    def title(self, ctx: McdocContext):
        name = self.identifier.split("::")[-1]
        return self.typeDef.title(name, ctx)


@dataclass
class DispatchResult:
    registry: str
    identifier: str
    typeDef: McdocType

    def title(self, ctx: McdocContext):
        name = f"{self.registry.removeprefix("minecraft:")} [{self.identifier}]"
        return self.typeDef.title(name, ctx)


class McdocSymbols:
    def __init__(self, data: dict):
        self.symbols = {
            str(key): deserialize_mcdoc(typeDef)
            for key, typeDef in data.get("mcdoc", {}).items()
        }
        self.dispatchers = {
            str(registry): {
                str(key): deserialize_mcdoc(typeDef)
                for key, typeDef in members.items()
            }
            for registry, members in data.get("mcdoc/dispatcher", {}).items()
        }

        self.names = defaultdict[str, list[str]](list)
        for key in self.symbols:
            name = key.split("::")[-1]
            self.names[name].append(key)
        self.names = dict(self.names)

    def search(self, query: str) -> Union[SymbolResult, DispatchResult]:
        if query in self.symbols:
            return SymbolResult(query, self.symbols[query])

        if query in self.names:
            identifier = self.names[query][0]
            return SymbolResult(identifier, self.symbols[identifier])

        parts = query.split(" ")
        if len(parts) == 2:
            registry, identifier = parts
            if ":" not in registry:
                registry = f"minecraft:{registry}"
            identifier = identifier.removeprefix("minecraft:")
            map = self.dispatchers.get(registry, None)
            if map and identifier in map:
                return DispatchResult(registry, identifier, map[identifier])
            raise QueryReturnedNoResults(query)

        identifier = query.removeprefix("minecraft:")
        resources = self.dispatchers.get("minecraft:resource", {})
        if query in resources:
            return DispatchResult("resource", identifier, resources[identifier])

        for registry, map in self.dispatchers.items():
            if identifier in map:
                return DispatchResult(registry, identifier, map[identifier])

        raise QueryReturnedNoResults(query)

    def get(self, path: str) -> Optional[McdocType]:
        return self.symbols.get(path, None)

    def dispatch(self, registry: str, identifier: str) -> Optional[McdocType]:
        return self.dispatchers.get(registry, {}).get(identifier, None)
