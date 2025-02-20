from collections import defaultdict
from dataclasses import dataclass
from typing import Optional, Union
import re

from commanderbot.ext.mcdoc.mcdoc_exceptions import QueryReturnedNoResults
from commanderbot.ext.mcdoc.mcdoc_types import McdocContext, McdocType, deserialize_mcdoc


@dataclass
class SymbolResult:
    identifier: str
    typeDef: McdocType

    def title(self, ctx: McdocContext):
        name = ctx.symbols.compact_path(self.identifier)
        return self.typeDef.title(name, ctx)
    
    def body(self, ctx: McdocContext):
        return self.typeDef.render(ctx)


@dataclass
class DispatchResult:
    registry: str
    identifier: str
    typeDef: McdocType

    def title(self, ctx: McdocContext):
        name = f"{self.registry.removeprefix("minecraft:")} [{self.identifier}]"
        return self.typeDef.title(name, ctx)
    
    def body(self, ctx: McdocContext):
        return self.typeDef.render(ctx)


@dataclass
class DisambiguationResult:
    query: str
    identifiers: list[str]

    def title(self, ctx: McdocContext):
        return f"{len(self.identifiers)} results for {self.query}"
    
    def body(self, ctx: McdocContext):
        return "\n".join([f"* {ctx.symbols.compact_path(i)}" for i in self.identifiers])


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
            parts = key.split("::")
            for i in range(len(parts)):
                name = "::".join(parts[i:])
                self.names[name].append(key)
        self.names = dict(self.names)

        self.unique_suffixes = dict[str, str]()
        for name, keys in self.names.items():
            if len(keys) <= 1 or re.match(r"<anonymous \d+>", name):
                continue
            for key in keys:
                parts = key.split("::")
                for i in reversed(range(len(parts)-1)):
                    suffix = "::".join(parts[i:])
                    if not [k for k in keys if k is not key and k.endswith(f"::{suffix}")]:
                        self.unique_suffixes[key] = suffix
                        break

    def search(self, query: str) -> Union[SymbolResult, DispatchResult, DisambiguationResult]:
        if query in self.symbols:
            return SymbolResult(query, self.symbols[query])

        if query in self.names:
            identifiers = self.names[query]
            if len(identifiers) > 1:
                return DisambiguationResult(query, identifiers)
            elif len(identifiers) == 1:
                return SymbolResult(identifiers[0], self.symbols[identifiers[0]])

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

    def compact_path(self, path: str) -> str:
        if path in self.unique_suffixes:
            return self.unique_suffixes[path]
        return path.split("::")[-1]

    def get(self, path: str) -> Optional[McdocType]:
        return self.symbols.get(path, None)

    def dispatch(self, registry: str, identifier: str) -> Optional[McdocType]:
        return self.dispatchers.get(registry, {}).get(identifier, None)
