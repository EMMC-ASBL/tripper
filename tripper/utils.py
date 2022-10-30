"""Utility functions."""
import hashlib
import inspect
import re
from typing import TYPE_CHECKING

from tripper.literal import Literal
from tripper.namespace import XSD

if TYPE_CHECKING:  # pragma: no cover
    from collections.abc import Mapping
    from typing import Any, Callable, Dict, Generator, Tuple, Union


def infer_iri(obj):
    """Return IRI of the individual that stands for object `obj`."""
    if isinstance(obj, str):
        return obj
    if hasattr(obj, "uri") and obj.uri:
        # dlite.Metadata or dataclass (or instance with uri)
        return obj.uri
    if hasattr(obj, "uuid") and obj.uuid:
        # dlite.Instance or dataclass
        return obj.uuid
    if hasattr(obj, "schema") and callable(obj.schema):
        # pydantic.BaseModel
        schema = obj.schema()
        properties = schema["properties"]
        if "uri" in properties and properties["uri"]:
            return properties["uri"]
        if "uuid" in properties and properties["uuid"]:
            return properties["uuid"]
    raise TypeError("cannot infer IRI from object {obj!r}")


def split_iri(iri: str) -> "Tuple[str, str]":
    """Split iri into namespace and name parts and return them as a tuple.

    Parameters:
        iri: The IRI to be split.

    Returns:
        A split IRI. Split into namespace and name.

    """
    if "#" in iri:
        namespace, name = iri.rsplit("#", 1)
        return f"{namespace}#", name

    if "/" in iri:
        namespace, name = iri.rsplit("/", 1)
        return f"{namespace}/", name

    raise ValueError("all IRIs should contain a slash")


def function_id(func: "Callable", length: int = 4) -> str:
    """Return a checksum for function `func`.

    The returned object is a string of hexadecimal digits.

    `length` is the number of bytes in the returned checksum.  Since
    the current implementation is based on the shake_128 algorithm,
    it make no sense to set `length` larger than 32 bytes.
    """
    return hashlib.shake_128(  # pylint: disable=too-many-function-args
        inspect.getsource(func).encode()
    ).hexdigest(length)


def en(value):  # pylint: disable=invalid-name
    """Convenience function that returns value as a plain english literal.

    Equivalent to``Literal(value, lang="en")``.
    """
    return Literal(value, lang="en")


def parse_literal(literal: "Any") -> "Literal":
    """Parse `literal` and return it as an instance of Literal.

    The main difference between this function and the Literal constructor,
    is that this function correctly interprets n3-encoded literal strings.
    """
    # pylint: disable=invalid-name,too-many-branches
    lang, datatype = None, None

    if isinstance(literal, Literal):
        return literal

    if not isinstance(literal, str):
        for type_, datatype in Literal.datatypes.items():
            if isinstance(literal, type_):
                return Literal(literal, lang=lang, datatype=datatype)
        TypeError(f"unsupported literal type: {type(literal)}")

    match = re.match(r'^\s*("""(.*)"""|"(.*)")\s*$', literal, flags=re.DOTALL)
    if match:
        _, v1, v2 = match.groups()
        value, datatype = v1 if v1 else v2, XSD.string
    else:
        match = re.match(
            r'^\s*("""(.*)"""|"(.*)")\^\^(.*)\s*$', literal, flags=re.DOTALL
        )
        if match:
            _, v1, v2, datatype = match.groups()
            value = v1 if v1 else v2
        else:
            match = re.match(
                r'^\s*("""(.*)"""|"(.*)")@(.*)\s*$', literal, flags=re.DOTALL
            )
            if match:
                _, v1, v2, lang = match.groups()
                value = v1 if v1 else v2
            else:
                value = literal

    if lang or datatype:
        if datatype:
            types = {v: k for k, v in Literal.datatypes.items()}
            type_ = types[datatype]
            try:
                value = type_(value)
            except TypeError:
                pass
        return Literal(value, lang=lang, datatype=datatype)

    for type_, datatype in Literal.datatypes.items():
        if type_ is not bool:
            try:
                return Literal(type_(literal), lang=lang, datatype=datatype)
            except (ValueError, TypeError):
                pass

    raise ValueError("cannot parse {literal=}")
