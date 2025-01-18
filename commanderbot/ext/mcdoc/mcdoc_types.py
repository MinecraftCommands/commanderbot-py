import json
from dataclasses import dataclass, field
from typing import Any, Callable, Mapping, Optional, Union

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

TEMPLATE_CHARS = ["🇦", "🇧", "🇨", "🇩", "🇪", "🇫", "🇬", "🇭", "🇮", "🇯", "🇰", "🇱", "🇲", "🇳", "🇴", "🇵", "🇶", "🇷", "🇸", "🇹", "🇺", "🇻", "🇼", "🇽", "🇾", "🇿"]

def cmp_version(a: str, b: str):
    return float(a[2:]) - float(b[2:])


@dataclass
class McdocContext:
    version: str
    lookup: Callable[[str], Optional["McdocType"]]
    compact: bool = False
    depth: int = 0
    type_mapping: Mapping[str, Union[str, "McdocType"]] = field(default_factory=dict)
    type_args: list["McdocType"] = field(default_factory=list)

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

    def allow_body(self):
        return self.depth <= 2

    def make_compact(self) -> "McdocContext":
        return McdocContext(self.version, self.lookup, True, self.depth, self.type_mapping, self.type_args)

    def nested(self) -> "McdocContext":
        return McdocContext(self.version, self.lookup, self.compact, self.depth + 1, self.type_mapping, self.type_args)

    def with_type_mapping(self, mapping: Mapping[str, Union[str, "McdocType"]]) -> "McdocContext":
        return McdocContext(self.version, self.lookup, self.compact, self.depth, mapping, self.type_args)

    def with_type_args(self, type_args: list["McdocType"]) -> "McdocContext":
        return McdocContext(self.version, self.lookup, self.compact, self.depth, self.type_mapping, type_args)


@dataclass
class Attribute:
    name: str
    value: Optional[dict]


@dataclass(kw_only=True)
class McdocBaseType:
    attributes: Optional[list[Attribute]] = None

    def has_attr(self, name: str):
        for a in self.attributes or []:
            if a.name == name:
                return True
        return False

    def get_attr(self, name: str) -> Optional[dict]:
        for a in self.attributes or []:
            if a.name == name:
                return a.value or dict()
        return None

    def title(self, name: str, ctx: McdocContext) -> str:
        return name

    def icons(self, ctx: McdocContext) -> list[str]:
        return [ICON_ANY]

    def prefix(self, ctx: McdocContext) -> str:
        return "".join(list(dict.fromkeys(self.icons(ctx))))

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

    def render(self):
        return f"[{'.'.join(f'`{a}`' if isinstance(a, str) else f'%{a.keyword}' for a in self.accessor)}]"


@dataclass
class StaticIndex:
    value: str

    def render(self):
        return self.value


@dataclass
class DispatcherType(McdocBaseType):
    registry: str
    parallelIndices: list[DynamicIndex | StaticIndex]

    def suffix(self, ctx):
        return f"{self.registry}[{','.join(i.render() for i in self.parallelIndices)}]"


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
            result += f"**?** {suffix}" if self.optional else f" {suffix}"
        elif self.optional:
            result += "**?**"
        desc = self.desc.strip() if self.desc else ""
        if desc:
            result += "".join(f"\n-# {d.strip()}" for d in desc.split("\n") if d.strip())
        if ctx.allow_body():
            body = self.type.body(ctx.make_compact())
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

    def filtered_fields(self, ctx: McdocContext):
        return [f for f in self.fields if ctx.filter(f.attributes)]

    def icons(self, ctx):
        return [ICON_STRUCT]

    def suffix(self, ctx):
        fields = self.filtered_fields(ctx)
        if not fields:
            return "*an empty object*"
        return "*an object*"

    def body_flat(self, ctx: McdocContext):
        results = []
        for field in self.filtered_fields(ctx):
            result = field.render(ctx)
            if result:
                results.append(result)
        if not results:
            return "*no fields*"
        joiner = "\n" if ctx.compact else "\n\n"
        return joiner.join(results)

    def body(self, ctx):
        lines = self.body_flat(ctx.nested())
        start = "" if ctx.compact else "\n"
        return start + "\n".join(f"> {line}" for line in lines.split("\n"))

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

    def filtered_values(self, ctx: McdocContext):
        return [v for v in self.values if ctx.filter(v.attributes)]

    def title(self, name, ctx):
        return f"enum {name}"

    def icons(self, ctx):
        return [LITERAL_ICONS[self.enumKind]]

    def suffix(self, ctx):
        values = self.filtered_values(ctx)
        if ctx.allow_body():
            return "*one of:*"
        if not values:
            return "*no options*"
        return f"*one of: {', '.join(json.dumps(v.value) for v in values)}*"

    def body_flat(self, ctx: McdocContext):
        if not ctx.allow_body():
            return ""
        results = []
        for field in self.filtered_values(ctx):
            result = self.prefix(ctx)
            result += f" `{field.identifier}`"
            result += f" = {json.dumps(field.value)}"
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

    def icons(self, ctx):
        if self.path in ctx.type_mapping:
            mapped = ctx.type_mapping[self.path]
            return mapped if isinstance(mapped, str) else mapped.icons(ctx)
        typeDef = ctx.symbol(self.path)
        if typeDef:
            return typeDef.icons(ctx)
        return super().icons(ctx)

    def suffix(self, ctx):
        if self.path in ctx.type_mapping:
            return ""
        return f"__{self.path.split('::')[-1]}__"


@dataclass
class UnionType(McdocBaseType):
    members: list["McdocType"]

    def filtered_members(self, ctx: McdocContext):
        return [m for m in self.members if ctx.filter(m.attributes)]

    def icons(self, ctx):
        all_icons: list[str] = []
        for member in self.filtered_members(ctx):
            all_icons.extend(member.icons(ctx))
        return list(dict.fromkeys(all_icons))

    def suffix(self, ctx):
        members = self.filtered_members(ctx)
        if not members:
            return "*nothing*"
        if len(members) == 1:
            return members[0].suffix(ctx)
        if ctx.allow_body():
            return "*one of:*"
        return f"*one of {len(members)} types*"

    def body(self, ctx):
        if not ctx.allow_body():
            return ""
        members = self.filtered_members(ctx)
        if not members:
            return ""
        if len(members) == 1:
            return members[0].body(ctx)
        results: list[str] = []
        for member in members:
            result = member.prefix(ctx)
            suffix = member.suffix(ctx)
            if suffix:
                result += f" {suffix}" if result else suffix
            if ctx.allow_body():
                body = member.body(ctx.make_compact().nested())
                if body:
                    body = "\n".join(f"  {line}" for line in body.split("\n"))
                    result += f"\n{body}" if result else body
            results.append(f"* {result}")
        return "\n".join(f"{'' if ctx.compact else '\n'}{r}" for r in results)


@dataclass
class TemplateType(McdocBaseType):
    child: "McdocType"
    typeParams: list[str]

    def abstract_mapping(self):
        mapping = dict[str, str]()
        used_chars = set[str]()
        for param in self.typeParams:
            letter = param.split('::')[-1][0].upper()
            preferred_char = TEMPLATE_CHARS[ord(letter) - ord('A')]
            if preferred_char in used_chars:
                for char in TEMPLATE_CHARS:
                    if char not in used_chars:
                        preferred_char = char
                        break
            mapping[param] = preferred_char
        return mapping

    def nest_context(self, ctx: McdocContext) -> McdocContext:
        if ctx.type_args:
            return ctx.with_type_mapping(dict(zip(self.typeParams, ctx.type_args))).with_type_args([])
        else:
            return ctx.with_type_mapping(self.abstract_mapping())

    def title(self, name, ctx) -> str:
        mapping = self.abstract_mapping()
        return f"{name} < {', '.join(mapping.values())} >"

    def icons(self, ctx):
        return self.child.icons(self.nest_context(ctx))

    def prefix(self, ctx):
        return self.child.prefix(self.nest_context(ctx))

    def suffix(self, ctx):
        return self.child.suffix(self.nest_context(ctx))

    def body(self, ctx):
        return self.child.body(self.nest_context(ctx))

    def render(self, ctx):
        return self.child.render(self.nest_context(ctx))


@dataclass
class ConcreteType(McdocBaseType):
    child: "McdocType"
    typeArgs: list["McdocType"]

    def nest_context(self, ctx: McdocContext) -> McdocContext:
        return ctx.with_type_args(self.typeArgs)

    def icons(self, ctx):
        return self.child.icons(self.nest_context(ctx))

    def prefix(self, ctx):
        return self.child.prefix(self.nest_context(ctx))

    def suffix(self, ctx):
        suffix = self.child.suffix(self.nest_context(ctx))
        if isinstance(self.child, ReferenceType):
            suffix += f" < {', '.join(t.prefix(self.nest_context(ctx)) for t in self.typeArgs)} >"
        return suffix

    def body(self, ctx):
        return self.child.body(self.nest_context(ctx))

    def render(self, ctx):
        return self.child.render(self.nest_context(ctx))


@dataclass
class NumericRange(McdocBaseType):
    min: Optional[float]
    max: Optional[float]
    minExcl: bool
    maxExcl: bool

    def render(self):
        if self.min is None:
            return f"below {self.max}" if self.maxExcl else f"at most {self.max}"
        if self.max is None:
            return f"above {self.min}" if self.minExcl else f"at least {self.min}"
        if self.minExcl and self.maxExcl:
            return f"between {self.min} and {self.max} (exclusive)"
        if self.minExcl:
            return f"above {self.min} and at most {self.max}"
        if self.maxExcl:
            return f"at least {self.min} and below {self.max}"
        if self.min == self.max:
            return f"exactly {self.min}"
        return f"between {self.min} and {self.max} (inclusive)"

    def render_length(self):
        if self.min == self.max:
            return f"of length {self.min}"
        else:
            return f"with length {self.render()}"


@dataclass
class StringType(McdocBaseType):
    lengthRange: Optional[NumericRange] = None

    def icons(self, ctx):
        return [ICON_STRING]

    def suffix(self, ctx):
        result = "a string"
        id = self.get_attr("id")
        if id is not None:
            if id["kind"] == "literal":
                registry = id["value"]["value"]
            elif id["kind"] == "tree":
                registry = id["values"]["registry"]["value"]["value"] # TODO
            else:
                registry = None
            result = "a resource location"
            if registry:
                result += f" ({registry})"
        elif self.has_attr("text_component"):
            result = "a stringified text component"
        elif self.has_attr("integer"):
            result = "a stringified integer"
        elif self.has_attr("regex_pattern"):
            result = "a regex pattern"
        elif self.has_attr("uuid"):
            result = "a hex uuid"
        elif self.has_attr("color"):
            result = "a hex color"
        elif self.has_attr("nbt"):
            result = "an SNBT string"
        elif self.has_attr("nbt_path"):
            result = "an NBT path"
        elif self.has_attr("team"):
            result = "a team name"
        elif self.has_attr("objective"):
            result = "a scoreboard objective"
        elif self.has_attr("tag"):
            result = "a command tag"
        elif self.has_attr("translation_key"):
            result = "a translation key"
        elif self.has_attr("entity"):
            result = "an entity selector"
        elif self.has_attr("command"):
            result = "a command"
        if self.lengthRange:
            result += f" with length {self.lengthRange.render()}"
        return f"*{result}*"


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

    def suffix(self, ctx):
        return "*anything*"


@dataclass
class UnsafeType(McdocBaseType):
    def icons(self, ctx):
        return [ICON_ANY]

    def suffix(self, ctx):
        return "*anything*"


@dataclass
class BooleanType(McdocBaseType):
    def icons(self, ctx):
        return [ICON_BOOLEAN]

    def suffix(self, ctx):
        return "*a boolean*"


@dataclass
class ByteType(McdocBaseType):
    valueRange: Optional[NumericRange] = None

    def icons(self, ctx):
        return [ICON_BYTE]

    def suffix(self, ctx):
        result = "a byte"
        if self.valueRange:
            result += f" {self.valueRange.render()}"
        return f"*{result}*"


@dataclass
class ShortType(McdocBaseType):
    valueRange: Optional[NumericRange] = None

    def icons(self, ctx):
        return [ICON_SHORT]

    def suffix(self, ctx):
        result = "a short"
        if self.valueRange:
            result += f" {self.valueRange.render()}"
        return f"*{result}*"


@dataclass
class IntType(McdocBaseType):
    valueRange: Optional[NumericRange] = None

    def icons(self, ctx):
        return [ICON_INT]

    def suffix(self, ctx):
        result = "an int"
        if self.valueRange:
            result += f" {self.valueRange.render()}"
        return f"*{result}*"


@dataclass
class LongType(McdocBaseType):
    valueRange: Optional[NumericRange] = None

    def icons(self, ctx):
        return [ICON_LONG]

    def suffix(self, ctx):
        result = "a long"
        if self.valueRange:
            result += f" {self.valueRange.render()}"
        return f"*{result}*"


@dataclass
class FloatType(McdocBaseType):
    valueRange: Optional[NumericRange] = None

    def icons(self, ctx):
        return [ICON_FLOAT]

    def suffix(self, ctx):
        result = "a float"
        if self.valueRange:
            result += f" {self.valueRange.render()}"
        return f"*{result}*"


@dataclass
class DoubleType(McdocBaseType):
    valueRange: Optional[NumericRange] = None

    def icons(self, ctx):
        return [ICON_DOUBLE]

    def suffix(self, ctx):
        result = "a double"
        if self.valueRange:
            result += f" {self.valueRange.render()}"
        return f"*{result}*"


@dataclass
class ByteArrayType(McdocBaseType):
    valueRange: Optional[NumericRange] = None
    lengthRange: Optional[NumericRange] = None

    def icons(self, ctx):
        return [ICON_BYTE_ARRAY]

    def suffix(self, ctx):
        result = "a byte array"
        if self.lengthRange:
            result += f" {self.lengthRange.render_length()}"
        if self.valueRange:
            if self.lengthRange:
                result += ", and"
            result += f" with values {self.valueRange.render()}"
        return f"*{result}*"


@dataclass
class IntArrayType(McdocBaseType):
    valueRange: Optional[NumericRange] = None
    lengthRange: Optional[NumericRange] = None

    def icons(self, ctx):
        return [ICON_INT_ARRAY]

    def suffix(self, ctx):
        result = "an int array"
        if self.lengthRange:
            result += f" {self.lengthRange.render_length()}"
        if self.valueRange:
            if self.lengthRange:
                result += ", and"
            result += f" with values {self.valueRange.render()}"
        return f"*{result}*"


@dataclass
class LongArrayType(McdocBaseType):
    valueRange: Optional[NumericRange] = None
    lengthRange: Optional[NumericRange] = None

    def icons(self, ctx):
        return [ICON_LONG_ARRAY]

    def suffix(self, ctx):
        result = "a long array"
        if self.lengthRange:
            result += f" {self.lengthRange.render_length()}"
        if self.valueRange:
            if self.lengthRange:
                result += ", and"
            result += f" with values {self.valueRange.render()}"
        return f"*{result}*"


@dataclass
class ListType(McdocBaseType):
    item: "McdocType"
    lengthRange: Optional[NumericRange] = None

    def icons(self, ctx):
        return [ICON_LIST]

    def suffix(self, ctx):
        result = "a list"
        if self.lengthRange:
            result += f" {self.lengthRange.render_length()}"
        else:
            result += " of"
        return f"*{result}:*"

    def body(self, ctx):
        result = self.item.prefix(ctx)
        suffix = self.item.suffix(ctx)
        if suffix:
            result += f" {suffix}" if result else suffix
        body = self.item.body(ctx.make_compact().nested())
        if body:
            body = "\n".join(f"  {line}" for line in body.split("\n"))
            result += f"\n{body}" if result else body
        return f"* {result}"


@dataclass
class TupleType(McdocBaseType):
    items: list["McdocType"]

    def icons(self, ctx):
        return [ICON_LIST]

    def suffix(self, ctx):
        return f"*a tuple of length {len(self.items)}:*"


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
    TemplateType,
    ConcreteType,
]


def deserialize_attributes(data: dict) -> list[Attribute]:
    result: list[Attribute] = []
    for attr in data.get("attributes", []):
        name = attr["name"]
        value = attr.get("value", None)
        result.append(Attribute(name=name,value=value))
    return result


def deserialize_numeric_range(data: Optional[dict]) -> Optional[NumericRange]:
    if data is None:
        return None
    kind = data.get("kind", 0)
    return NumericRange(
        min=data.get("min", None),
        max=data.get("max", None),
        minExcl=(kind & 0b10) != 0,
        maxExcl=(kind & 0b01) != 0,
    )


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
        return ByteType(
            valueRange=deserialize_numeric_range(data.get("valueRange")),
            attributes=deserialize_attributes(data),
        )
    if kind == "short":
        return ShortType(
            valueRange=deserialize_numeric_range(data.get("valueRange")),
            attributes=deserialize_attributes(data),
        )
    if kind == "int":
        return IntType(
            valueRange=deserialize_numeric_range(data.get("valueRange")),
            attributes=deserialize_attributes(data),
        )
    if kind == "long":
        return LongType(
            valueRange=deserialize_numeric_range(data.get("valueRange")),
            attributes=deserialize_attributes(data),
        )
    if kind == "float":
        return FloatType(
            valueRange=deserialize_numeric_range(data.get("valueRange")),
            attributes=deserialize_attributes(data),
        )
    if kind == "double":
        return DoubleType(
            valueRange=deserialize_numeric_range(data.get("valueRange")),
            attributes=deserialize_attributes(data),
        )
    if kind == "reference":
        return ReferenceType(
            path=data.get("path", ""),
            attributes=deserialize_attributes(data),
        )
    if kind == "union":
        return UnionType(
            members=[deserialize_mcdoc(member) for member in data.get("members", [])],
            attributes=deserialize_attributes(data),
        )
    if kind == "string":
        return StringType(
            lengthRange=deserialize_numeric_range(data.get("lengthRange")),
            attributes=deserialize_attributes(data),
        )
    if kind == "list":
        return ListType(
            item=deserialize_mcdoc(data["item"]),
            lengthRange=deserialize_numeric_range(data.get("lengthRange")),
            attributes=deserialize_attributes(data),
        )
    if kind == "tuple":
        return TupleType(
            items=[deserialize_mcdoc(e) for e in data["items"]],
            attributes=deserialize_attributes(data),
        )
    if kind == "byte_array":
        return ByteArrayType(
            lengthRange=deserialize_numeric_range(data.get("lengthRange")),
            valueRange=deserialize_numeric_range(data.get("valueRange")),
            attributes=deserialize_attributes(data),
        )
    if kind == "int_array":
        return IntArrayType(
            lengthRange=deserialize_numeric_range(data.get("lengthRange")),
            valueRange=deserialize_numeric_range(data.get("valueRange")),
            attributes=deserialize_attributes(data),
        )
    if kind == "long_array":
        return LongArrayType(
            lengthRange=deserialize_numeric_range(data.get("lengthRange")),
            valueRange=deserialize_numeric_range(data.get("valueRange")),
            attributes=deserialize_attributes(data),
        )
    if kind == "template":
        return TemplateType(
            child=deserialize_mcdoc(data["child"]),
            typeParams=[t["path"] for t in data["typeParams"]],
            attributes=deserialize_attributes(data),
        )
    if kind == "concrete":
        return ConcreteType(
            child=deserialize_mcdoc(data["child"]),
            typeArgs=[deserialize_mcdoc(t) for t in data["typeArgs"]],
            attributes=deserialize_attributes(data),
        )
    raise ValueError(f"Unknown kind: {kind}")
