import json
from dataclasses import dataclass
from typing import Union, Optional, Any, Callable

ICON_ANY = "<:any:1328878339305246761>"
ICON_BOOLEAN = "<:boolean:1328844824824254475>"
ICON_BYTE = "<:byte:1328844842469425264>"
ICON_BYTE_ARRAY = "<:byte_array:1328844856713412758>"
ICON_DOUBLE = "<:double:1328844873205547028>"
ICON_FLOAT = "<:float:1328844885276622858>"
ICON_INT = "<:int:1328844896903237634>"
ICON_INT_ARRAY = "<:int_array:1328844908898812004>"
ICON_LIST = "<:list:1328844919665856622>"
ICON_LONG = "<:long:1328844930998730812>"
ICON_LONG_ARRAY = "<:long_array:1328844941706793022>"
ICON_SHORT = "<:short:1328844953757028382>"
ICON_STRING = "<:string:1328844965161467956>"
ICON_STRUCT = "<:struct:1328844974661435546>"

LITERAL_ICONS = {
    "boolean": ICON_BOOLEAN,
    "byte": ICON_BYTE,
    "short": ICON_SHORT,
    "int": ICON_INT,
    "long": ICON_LONG,
    "float": ICON_FLOAT,
    "double": ICON_DOUBLE,
    "string": ICON_STRING,
}


def cmp_version(a: str, b: str):
    return float(a[2:]) - float(b[2:])


class McdocContext:
    def __init__(self, version: str, lookup: Callable[[str], Optional["McdocType"]]):
        self.version = version
        self.lookup = lookup

    def symbol(self, path: str):
        return self.lookup(path)

    def filter(self, attributes: Optional[list["Attribute"]]):
        if not attributes:
            return True
        since = next((a.value for a in attributes if a.name == "since"), None)
        if since and cmp_version(self.version, since["value"]["value"]) < 0:
            return False
        until = next((a.value for a in attributes if a.name == "until"), None)
        if until and cmp_version(self.version, until["value"]["value"]) >= 0:
            return False
        return True


@dataclass
class Attribute:
    name: str
    value: Optional[dict]


@dataclass(kw_only=True)
class McdocBaseType:
    attributes: Optional[list[Attribute]] = None

    def icons(self, ctx: McdocContext) -> list[str]:
        return [ICON_ANY]

    def prefix(self, ctx: McdocContext) -> str:
        return "".join(set(self.icons(ctx)))

    def suffix(self, ctx: McdocContext) -> str:
        return ""

    def body(self, ctx: McdocContext) -> str:
        return ""

    def render(self, ctx: McdocContext) -> str:
        result = self.prefix(ctx)
        suffix = self.suffix(ctx)
        if suffix:
            result += f" {suffix}" if result else suffix
        body = self.body(ctx)
        if body:
            result += f"\n{body}" if result else body
        return result


@dataclass
class KeywordIndex:
    keyword: str


@dataclass
class DynamicIndex:
    accessor: list[str | KeywordIndex]


@dataclass
class StaticIndex:
    value: str


@dataclass
class DispatcherType(McdocBaseType):
    registry: str
    parallelIndices: list[DynamicIndex | StaticIndex]

    def suffix(self, ctx):
        return f"{self.registry}[{self.parallelIndices}]"


@dataclass
class StructTypePairField:
    key: Union[str, "McdocType"]
    type: "McdocType"
    optional: bool = False
    deprecated: bool = False
    desc: Optional[str] = None
    attributes: Optional[list[Attribute]] = None

    def is_deprecated(self, ctx: McdocContext):
        if self.deprecated:
            return True
        deprecated = next((a.value for a in self.attributes or [] if a.name == "deprecated"), None)
        if deprecated:
            return cmp_version(ctx.version, deprecated["value"]["value"]) >= 0
        return False

    def render(self, ctx: McdocContext):
        if isinstance(self.key, str):
            key = self.key
        elif isinstance(self.key, LiteralType):
            key = str(self.key.value)
        else:
            return ""
        key = f"`{key}`"
        if self.is_deprecated(ctx):
            key = f"~~{key}~~"
        result = self.type.prefix(ctx)
        result += f" {key}" if result else key
        suffix = self.type.suffix(ctx)
        if suffix:
            result += f"?: {suffix}" if self.optional else f": {suffix}"
        elif self.optional:
            result += "?"
        desc = self.desc.strip() if self.desc else ""
        if desc:
            result += "".join(f"\n-# {d.strip()}" for d in desc.split("\n") if d.strip())
        body = self.type.body(ctx)
        if body:
            result += f"\n{body}"
        return result


@dataclass
class StructTypeSpreadField:
    type: "McdocType"
    attributes: Optional[list[Attribute]] = None

    def render(self, ctx: McdocContext):
        match self.type:
            case StructType():
                return self.type.body_flat(ctx)
            case DispatcherType(parallelIndices=[DynamicIndex(accessor=[str(s)])]):
                return f"*more fields depending on the value of `{s}`*"

        suffix = self.type.suffix(ctx)
        if suffix:
            return f"*all fields from {suffix}*"

        return ""


@dataclass
class StructType(McdocBaseType):
    fields: list[StructTypePairField | StructTypeSpreadField]

    def icons(self, ctx):
        return [ICON_STRUCT]

    def body_flat(self, ctx: McdocContext):
        results = []
        for field in self.fields:
            if ctx.filter(field.attributes):
                result = field.render(ctx)
                if result:
                    results.append(result)
        if not results:
            return "*no fields*"
        return "\n\n".join(results)

    def body(self, ctx):
        lines = self.body_flat(ctx)
        return "".join(f"\n> {line}" for line in lines.split("\n"))

    def render(self, ctx):
        return self.body_flat(ctx)

@dataclass
class EnumTypeField:
    identifier: str
    value: str | float
    desc: Optional[str] = None
    attributes: Optional[list[Attribute]] = None

@dataclass
class EnumType(McdocBaseType):
    enumKind: str
    values: list[EnumTypeField]

    def icons(self, ctx):
        return [LITERAL_ICONS[self.enumKind]]

    def body_flat(self, ctx: McdocContext):
        results = []
        for field in self.values:
            if ctx.filter(field.attributes):
                result = self.prefix(ctx)
                result += f" `{field.identifier}`"
                result += f" = {field.value}"
                desc = field.desc.strip() if field.desc else ""
                if desc:
                    result += "".join(f"\n-# {d.strip()}" for d in desc.split("\n") if d.strip())
                results.append(result)
        if not results:
            return "*no options*"
        return "\n".join(results)

    def body(self, ctx):
        lines = self.body_flat(ctx)
        return "\n".join(f"> {line}" for line in lines.split("\n"))

    def render(self, ctx):
        return self.body_flat(ctx)


@dataclass
class ReferenceType(McdocBaseType):
    path: str

    def suffix(self, ctx):
        return self.path.split("::")[-1]


@dataclass
class UnionType(McdocBaseType):
    members: list["McdocType"]

    def filtered_members(self, ctx: McdocContext):
        return [m for m in self.members if ctx.filter(m.attributes)]

    def icons(self, ctx):
        all_icons: list[str] = []
        for member in self.filtered_members(ctx):
            all_icons.extend(member.icons(ctx))
        return list(set(all_icons))


@dataclass
class IndexedType(McdocBaseType):
    parallelIndices: list[Any]
    child: "McdocType"


@dataclass
class TemplateType(McdocBaseType):
    child: "McdocType"
    typeParams: list[dict[str, str]]


@dataclass
class ConcreteType(McdocBaseType):
    child: "McdocType"
    typeArgs: list["McdocType"]


@dataclass
class MappedType(McdocBaseType):
    child: "McdocType"
    mapping: dict[str, "McdocType"]


@dataclass
class StringType(McdocBaseType):
    lengthRange: Optional[Any] = None

    def icons(self, ctx):
        return [ICON_STRING]


@dataclass
class LiteralType(McdocBaseType):
    kind: str
    value: bool | str | float

    def icons(self, ctx):
        return [LITERAL_ICONS.get(self.kind, ICON_ANY)]
    
    def suffix(self, ctx):
        return json.dumps(self.value)


@dataclass
class AnyType(McdocBaseType):
    def icons(self, ctx):
        return [ICON_ANY]


@dataclass
class UnsafeType(McdocBaseType):
    def icons(self, ctx):
        return [ICON_ANY]


@dataclass
class BooleanType(McdocBaseType):
    def icons(self, ctx):
        return [ICON_BOOLEAN]


@dataclass
class ByteType(McdocBaseType):
    valueRange: Optional[Any] = None

    def icons(self, ctx):
        return [ICON_BYTE]


@dataclass
class ShortType(McdocBaseType):
    valueRange: Optional[Any] = None

    def icons(self, ctx):
        return [ICON_SHORT]


@dataclass
class IntType(McdocBaseType):
    valueRange: Optional[Any] = None

    def icons(self, ctx):
        return [ICON_INT]


@dataclass
class LongType(McdocBaseType):
    valueRange: Optional[Any] = None

    def icons(self, ctx):
        return [ICON_LONG]


@dataclass
class FloatType(McdocBaseType):
    valueRange: Optional[Any] = None

    def icons(self, ctx):
        return [ICON_FLOAT]


@dataclass
class DoubleType(McdocBaseType):
    valueRange: Optional[Any] = None

    def icons(self, ctx):
        return [ICON_DOUBLE]


@dataclass
class ByteArrayType(McdocBaseType):
    valueRange: Optional[Any] = None
    lengthRange: Optional[Any] = None

    def icons(self, ctx):
        return [ICON_BYTE_ARRAY]


@dataclass
class IntArrayType(McdocBaseType):
    valueRange: Optional[Any] = None
    lengthRange: Optional[Any] = None

    def icons(self, ctx):
        return [ICON_INT_ARRAY]


@dataclass
class LongArrayType(McdocBaseType):
    valueRange: Optional[Any] = None
    lengthRange: Optional[Any] = None

    def icons(self, ctx):
        return [ICON_LONG_ARRAY]


@dataclass
class ListType(McdocBaseType):
    item: "McdocType"
    lengthRange: Optional[Any] = None

    def icons(self, ctx):
        return [ICON_LIST]


@dataclass
class TupleType(McdocBaseType):
    items: list["McdocType"]

    def icons(self, ctx):
        return [ICON_LIST]


McdocType = Union[
    DispatcherType,
    EnumType,
    ListType,
    LiteralType,
    AnyType,
    UnsafeType,
    BooleanType,
    ByteType,
    ShortType,
    IntType,
    LongType,
    FloatType,
    DoubleType,
    ByteArrayType,
    IntArrayType,
    LongArrayType,
    ReferenceType,
    StringType,
    StructType,
    TupleType,
    UnionType,
    IndexedType,
    TemplateType,
    ConcreteType,
    MappedType
]


def deserialize_attributes(data: dict) -> list[Attribute]:
    result: list[Attribute] = []
    for attr in data.get("attributes", []):
        name = attr["name"]
        value = attr.get("value", None)
        result.append(Attribute(name=name,value=value))
    return result


def deserialize_mcdoc(data: dict) -> McdocType:
    kind = data.get("kind")

    if kind == "dispatcher":
        parallelIndices: list[DynamicIndex | StaticIndex] = []
        for index in data.get("parallelIndices", []):
            if index["kind"] == "dynamic":
                accessor: list[str | KeywordIndex] = []
                for part in index["accessor"]:
                    if isinstance(part, str):
                        accessor.append(part)
                    else:
                        accessor.append(KeywordIndex(part["keyword"]))
                parallelIndices.append(DynamicIndex(accessor=accessor))
            elif index["kind"] == "static":
                parallelIndices.append(StaticIndex(value=index["value"]))
        return DispatcherType(
            registry=data.get("registry", ""),
            parallelIndices=parallelIndices,
            attributes=deserialize_attributes(data),
        )
    if kind == "struct":
        fields = []
        for f in data.get("fields", []):
            if "key" in f:
                key = f["key"]
                if isinstance(key, dict):
                    key = deserialize_mcdoc(key)
                fields.append(StructTypePairField(
                    key=key,
                    type=deserialize_mcdoc(f["type"]),
                    optional=f.get("optional", False),
                    deprecated=f.get("deprecated", False),
                    desc=f.get("desc"),
                    attributes=deserialize_attributes(f),
                ))
            else:
                fields.append(StructTypeSpreadField(
                    type=deserialize_mcdoc(f.get("type")),
                    attributes=deserialize_attributes(f),
                ))
        return StructType(fields, attributes=deserialize_attributes(data))
    if kind == "enum":
        values = []
        for v in data.get("values", []):
            values.append(EnumTypeField(
                identifier=v["identifier"],
                value=v["value"],
                desc=v.get("desc"),
                attributes=deserialize_attributes(v),
            ))
        return EnumType(
            enumKind=data["enumKind"],
            values=values,
            attributes=deserialize_attributes(data),
        )
    if kind == "literal":
        return LiteralType(
            kind=data["value"]["kind"],
            value=data["value"]["value"],
            attributes=deserialize_attributes(data)
        )
    if kind == "any":
        return AnyType(attributes=deserialize_attributes(data))
    if kind == "unsafe":
        return AnyType(attributes=deserialize_attributes(data))
    if kind == "boolean":
        return BooleanType(attributes=deserialize_attributes(data))
    if kind == "byte":
        return ByteType(valueRange=data.get("valueRange"), attributes=deserialize_attributes(data))
    if kind == "short":
        return ShortType(valueRange=data.get("valueRange"), attributes=deserialize_attributes(data))
    if kind == "int":
        return IntType(valueRange=data.get("valueRange"), attributes=deserialize_attributes(data))
    if kind == "long":
        return LongType(valueRange=data.get("valueRange"), attributes=deserialize_attributes(data))
    if kind == "float":
        return FloatType(valueRange=data.get("valueRange"), attributes=deserialize_attributes(data))
    if kind == "double":
        return DoubleType(valueRange=data.get("valueRange"), attributes=deserialize_attributes(data))
    if kind == "reference":
        return ReferenceType(data.get("path", ""), attributes=deserialize_attributes(data))
    if kind == "union":
        return UnionType(
            members=[deserialize_mcdoc(member) for member in data.get("members", [])],
            attributes=deserialize_attributes(data),
        )
    if kind == "string":
        return StringType(lengthRange=data.get("lengthRange"), attributes=deserialize_attributes(data))
    if kind == "list":
        return ListType(
            item=deserialize_mcdoc(data["item"]),
            lengthRange=data.get("lengthRange"),
            attributes=deserialize_attributes(data),
        )
    if kind == "tuple":
        return TupleType(
            items=[deserialize_mcdoc(e) for e in data["items"]],
            attributes=deserialize_attributes(data),
        )
    if kind == "byte_array":
        return ByteArrayType(attributes=deserialize_attributes(data)) # TODO
    if kind == "int_array":
        return IntArrayType(attributes=deserialize_attributes(data)) # TODO
    if kind == "long_array":
        return LongArrayType(attributes=deserialize_attributes(data)) # TODO
    if kind == "template":
        return TemplateType(
            child=deserialize_mcdoc(data["child"]),
            typeParams=[], # TODO
            attributes=deserialize_attributes(data),
        )
    if kind == "concrete":
        return ConcreteType(
            child=deserialize_mcdoc(data["child"]),
            typeArgs=[], # TODO
            attributes=deserialize_attributes(data),
        )
    raise ValueError(f"Unknown kind: {kind}")
