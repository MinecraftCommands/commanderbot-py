from collections import defaultdict
from dataclasses import dataclass
from typing import Optional

from commanderbot.ext.mcdoc.mcdoc_types import McdocType, deserialize_mcdoc

@dataclass
class McdocSymbol:
    identifier: str
    typeDef: McdocType


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

    def search(self, query: str) -> Optional[McdocSymbol]:
        if query in self.symbols:
            return McdocSymbol(query, self.symbols[query])

        if query in self.names:
            identifier = self.names[query][0]
            return McdocSymbol(identifier, self.symbols[identifier])

        # TODO: search dispatchers
        return None
    
    def get(self, path: str) -> Optional[McdocType]:
        return self.symbols.get(path, None)
