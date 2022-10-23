"""Literal rdf values."""
import re
import warnings
from datetime import datetime
from typing import TYPE_CHECKING

from .namespace import OWL, RDF, RDFS, XSD

if TYPE_CHECKING:  # pragma: no cover
    from typing import Any, Tuple, Union


class Literal(str):
    """A literal RDF value."""

    lang: str
    datatype: "Any"

    datatypes = {
        datetime: XSD.dateTime,
        int: XSD.integer,
        float: XSD.double,
        bytes: XSD.hexBinary,
        bytearray: XSD.hexBinary,
        str: XSD.string,
        bool: XSD.boolean,
    }

    def __new__(cls, value, lang=None, datatype=None):
        string = super().__new__(cls, value)
        if lang:
            if datatype:
                raise TypeError("A literal can only have one of `lang` or `datatype`.")
            string.lang = str(lang)
            string.datatype = None
        else:
            string.lang = None
            if datatype:
                string.datatype = cls.datatypes.get(datatype, datatype)
            elif isinstance(value, str):
                string.datatype = None
            elif isinstance(value, bool):
                string.datatype = XSD.boolean
            elif isinstance(value, int):
                string.datatype = XSD.integer
            elif isinstance(value, float):
                string.datatype = XSD.double
            elif isinstance(value, (bytes, bytearray)):
                string = value.hex()
                string.datatype = XSD.hexBinary
            elif isinstance(value, datetime):
                string.datatype = XSD.dateTime
                # TODO:
                #   - XSD.base64Binary
                #   - XSD.byte, XSD.unsignedByte
            else:
                string.datatype = None
        return string

    def __repr__(self):
        lang = f", lang='{self.lang}'" if self.lang else ""
        datatype = f", datatype='{self.datatype}'" if self.datatype else ""
        return f"Literal('{self}'{lang}{datatype})"

    value = property(
        fget=lambda self: self.to_python(),
        doc="Appropriate python datatype derived from this RDF literal.",
    )

    def to_python(self):
        """Returns an appropriate python datatype derived from this RDF
        literal."""
        value = str(self)

        if self.datatype == XSD.boolean:
            value = bool(self)
        elif self.datatype in (
            XSD.integer,
            XSD.int,
            XSD.short,
            XSD.long,
            XSD.nonPositiveInteger,
            XSD.negativeInteger,
            XSD.nonNegativeInteger,
            XSD.unsignedInt,
            XSD.unsignedShort,
            XSD.unsignedLong,
            XSD.byte,
            XSD.unsignedByte,
        ):
            value = int(self)
        elif self.datatype in (
            XSD.double,
            XSD.decimal,
            XSD.dataTimeStamp,
            OWL.real,
            OWL.rational,
        ):
            value = float(self)
        elif self.datatype == XSD.hexBinary:
            value = self.encode()
        elif self.datatype == XSD.dateTime:
            value = datetime.fromisoformat(self)
        elif self.datatype and self.datatype not in (
            RDF.PlainLiteral,
            RDF.XMLLiteral,
            RDFS.Literal,
            XSD.anyURI,
            XSD.language,
            XSD.Name,
            XSD.NMName,
            XSD.normalizedString,
            XSD.string,
            XSD.token,
            XSD.NMTOKEN,
        ):
            warnings.warn(f"unknown datatype: {self.datatype} - assuming string")
        return value

    def n3(self):  # pylint: disable=invalid-name
        """Returns a representation in n3 format."""
        if self.lang:
            return f'"{self}"@{self.lang}'
        if self.datatype:
            return f'"{self}"^^{self.datatype}'
        return f'"{self}"'


def en(value):  # pylint: disable=invalid-name
    """Convenience function that returns value as a plain english literal.

    Equivalent to``Literal(value, lang="en")``.
    """
    return Literal(value, lang="en")


def parse_literal(
    literal: "Union[str, Literal]",
) -> "Tuple[Any, Union[str, None], Union[str, None]]":
    """Parses n3-encoded literal and return a (value, lang, datatype) tuple."""
    # pylint: disable=invalid-name
    lang, datatype = None, None

    if isinstance(literal, Literal):
        return literal.value, literal.lang, literal.datatype

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
            value = type_(value)
        return value, lang, datatype

    for type_, datatype in Literal.datatypes.items():
        try:
            value = type_(literal)
        except (ValueError, TypeError):
            pass
        else:
            return value, lang, datatype

    raise ValueError("cannot parse {literal=}")
