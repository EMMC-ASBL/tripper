"""Utility functions."""

# pylint: disable=invalid-name,redefined-builtin
import datetime
import hashlib
import inspect
import random
import re
import string
from typing import TYPE_CHECKING

from tripper.literal import Literal
from tripper.namespace import XSD

if TYPE_CHECKING:  # pragma: no cover
    from typing import Any, Callable, Tuple, Union

    # There
    OptionalTriple = Tuple[
        Union[str, None], Union[str, None], Union[str, Any, None]
    ]
    Triple = Tuple[str, str, Union[str, Any]]


__all__ = (
    "infer_iri",
    "split_iri",
    "function_id",
    "en",
    "parse_literal",
    "parse_object",
    "as_python",
    "check",
    "random_string",
)


def infer_iri(obj):
    """Return IRI of the individual that stands for object `obj`."""

    # Please note that tripper does not depend on neither DLite nor Pydantic.
    # Hence neither of these packages are imported.  However, due to duck-
    # typing, infer_iri() is still able to recognise DLite and Pydantic
    # objects and infer their IRIs.

    if isinstance(obj, str):
        iri = obj
    elif hasattr(obj, "uri") and isinstance(obj.uri, str):
        # dlite.Metadata or dataclass (or instance with uri)
        iri = obj.uri
    elif hasattr(obj, "uuid") and obj.uuid:
        # dlite.Instance or dataclass
        iri = str(obj.uuid)
    elif hasattr(obj, "schema") and callable(obj.schema):
        # pydantic.BaseModel
        if hasattr(obj, "identity") and isinstance(obj.identity, str):
            # soft7 pydantic model
            iri = obj.identity
        else:
            # pydantic instance
            schema = obj.schema()
            properties = schema["properties"]
            if "uri" in properties and isinstance(properties["uri"], str):
                iri = properties["uri"]
            if "identity" in properties and isinstance(
                properties["identity"], str
            ):
                iri = properties["identity"]
            if "uuid" in properties and properties["uuid"]:
                iri = str(properties["uuid"])
    else:
        raise TypeError(f"cannot infer IRI from object: {obj!r}")
    return str(iri)


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
    source = inspect.getsource(func)
    doc = func.__doc__ if func.__doc__ else ""
    return hashlib.shake_128(  # pylint: disable=too-many-function-args
        (source + doc).encode()
    ).hexdigest(length)


def en(value) -> "Literal":  # pylint: disable=invalid-name
    """Convenience function that returns value as a plain english literal.

    Equivalent to ``Literal(value, lang="en")``.
    """
    return Literal(value, lang="en")


def parse_literal(literal: "Any") -> "Any":
    """Parse Python object `literal` and return it as an instance of Literal.

    The main difference between this function and the Literal constructor,
    is that this function correctly interprets n3-encoded literal strings.
    """
    # pylint: disable=invalid-name,too-many-branches,too-many-return-statements
    lang, datatype = None, None

    if isinstance(literal, Literal):
        return literal

    if hasattr(literal, "lang"):
        lang = literal.lang
    elif hasattr(literal, "language"):
        lang = literal.language

    if (
        not lang
        and hasattr(literal, "datatype")
        and literal.datatype is not None
    ):
        datatype = str(literal.datatype)

    # This will handle rdflib literals correctly and probably most other
    # literal representations as well.
    if hasattr(literal, "value"):
        return Literal(literal.value, lang=lang, datatype=datatype)

    if not isinstance(literal, str):
        if isinstance(literal, tuple(Literal.datatypes)):
            return Literal(
                literal,
                lang=lang,
                datatype=Literal.datatypes.get(type(literal))[
                    0
                ],  # type: ignore
            )
        raise TypeError(f"unsupported literal type: {type(literal)}")

    if hasattr(literal, "n3") and callable(literal.n3):
        return parse_literal(literal.n3())

    match = re.match(r'^\s*("""(.*)"""|"(.*)")\s*$', literal, flags=re.DOTALL)
    if match:
        _, v1, v2 = match.groups()
        value, datatype = v1 if v1 else v2, XSD.string
    else:
        match = re.match(
            r'^\s*("""(.*)"""|"(.*)")\^\^(<([^>]+)>|([^<].*))\s*$',
            literal,
            flags=re.DOTALL,
        )
        if match:
            _, v1, v2, _, d1, d2 = match.groups()
            value = v1 if v1 else v2
            datatype = d1 if d1 else d2
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
            types = {}
            for pytype, datatypes in Literal.datatypes.items():
                types.update({t: pytype for t in datatypes})
            type_ = types.get(datatype, str)
            if type_ is bool and value in ("False", "false", "0", 0, False):
                return Literal(False)
            try:
                value = type_(value)
            except TypeError:
                pass
        return Literal(value, lang=lang, datatype=datatype)

    for type_, datatypes in Literal.datatypes.items():
        if type_ is not bool:
            try:
                return Literal(
                    type_(literal), lang=lang, datatype=datatypes[0]
                )
            except (ValueError, TypeError):
                pass

    raise ValueError(f'cannot parse literal "{literal}"')


# Note:
# The return type of parse_object() should really be "Union[str,
# Literal]", but the current version of mypy interprets `Literal` as
# `typing.Literal`, resulting in mypy reporting a lot of false errors.
# It even doesn't understand if we write "Union[str, tripper.Literal".
# Changing to `Any` solves the problem, to the price of loosing
# accuracy...
#
def parse_object(obj: "Union[str, Literal]") -> "Union[str, Any]":
    """Applies heuristics to parse RDF object `obj` to an IRI or literal.

    The following heuristics is performed (in the given order):
    - If `obj` is a Literal, it is returned.
    - If `obj` is a string and
      - starts with "_:", it is assumed to be a blank node and returned.
      - starts with a scheme, it is asumed to be an IRI and returned.
      - can be converted to a float, int or datetime, it is returned
        converted to a literal of the corresponding type.
      - it is a valid n3 representation, return it as the given type.
      - otherwise, return it as a xsd:string literal.
    - Otherwise, raise an ValueError.

    Returns
        A string if `obj` is considered to be an IRI, otherwise a
        literal.
    """
    # pylint: disable=too-many-return-statements
    if isinstance(obj, Literal):
        return obj
    if isinstance(obj, str):
        if obj.startswith("_:") or re.match(r"^[a-z]+://", obj):  # IRI
            return obj
        if obj in ("true", "false"):  # boolean
            return Literal(obj, datatype=XSD.boolean)
        if re.match(r"^\s*[+-]?\d+\s*$", obj):  # integer
            return Literal(obj, datatype=XSD.integer)
        if check(float, obj, ValueError):  #  float
            return Literal(obj, datatype=XSD.double)
        if check(
            datetime.datetime.fromisoformat, obj, ValueError
        ):  #  datetime
            return Literal(obj, datatype=XSD.dateTime)
        return parse_literal(obj)
    raise ValueError("`obj` should be a literal or a string.")


def as_python(value: "Any") -> "Any":
    """Converts `value` to a native Python representation.

    If `value` is a Literal, its Python representation will be returned.
    If `value` is a string, it will first be converted to a Literal, before
    its Python representation is returned.
    Otherwise, `value` will be returned as-is.
    """
    if isinstance(value, Literal):
        return value.to_python()
    if isinstance(value, str):
        return parse_literal(value).to_python()
    return value


def check(func: "Callable", s: str, exceptions) -> bool:
    """Help function returning true if `func(s)` does not raise an exception.

    False is returned if `func(s)` raises an exception listed in `exceptions`.
    Otherwise the exception is propagated.
    """
    # Note that the missing type hint on `exceptions` is deliberate, see
    # https://peps.python.org/pep-0484/#exceptions
    try:
        func(s)
    except exceptions:
        return False
    return True


def random_string(length=8):
    """Return a random string of the given length."""
    letters = string.ascii_letters + string.digits
    return "".join(random.choice(letters) for i in range(length))  # nosec
