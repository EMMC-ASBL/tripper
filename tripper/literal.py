"""Literal rdf values."""

import warnings
from datetime import datetime
from typing import TYPE_CHECKING

from tripper.namespace import RDF, RDFS, XSD

if TYPE_CHECKING:  # pragma: no cover
    from typing import Any, Optional, Union


class Literal(str):
    """A literal RDF value.

    Arguments:
        value (Union[datetime, bytes, bytearray, bool, int, float, str]):
            The literal value. See the `datatypes` class attribute for valid
            supported data types.  A localised string is provided as a string
            with `lang` set to a language code.
        lang (Optional[str]): A standard language code, like "en", "no", etc.
            Implies that the `value` is a localised string.
        datatype (Any): Explicit specification of the type of `value`. Should
            not be combined with `lang`.
    """

    lang: "Union[str, None]"
    datatype: "Any"

    # Note that the order of datatypes matters - it is used by
    # utils.parse_literal() when inferring the datatype of a literal.
    datatypes = {
        datetime: (XSD.dateTime,),
        bytes: (XSD.hexBinary,),
        bytearray: (XSD.hexBinary,),
        bool: (XSD.boolean,),
        int: (
            XSD.integer,
            XSD.int,
            XSD.short,
            XSD.long,
            XSD.nonNegativeInteger,
            XSD.nonPositiveInteger,
            XSD.negativeInteger,
            XSD.unsignedInt,
            XSD.unsignedShort,
            XSD.unsignedLong,
            XSD.byte,
            XSD.unsignedByte,
        ),
        float: (
            XSD.double,
            XSD.decimal,
            XSD.dateTimeStamp,
            XSD.real,
            XSD.rational,
        ),
        str: (
            XSD.string,
            RDF.HTML,
            RDF.PlainLiteral,
            RDF.XMLLiteral,
            RDFS.Literal,
            XSD.anyURI,
            XSD.language,
            XSD.Name,
            XSD.NMName,
            XSD.normalizedString,
            XSD.token,
            XSD.NMTOKEN,
        ),
    }

    def __new__(
        cls,
        value: "Union[datetime, bytes, bytearray, bool, int, float, str]",
        lang: "Optional[str]" = None,
        datatype: "Optional[Any]" = None,
    ):
        # pylint: disable=too-many-branches
        string = super().__new__(cls, value)
        string.lang = None
        string.datatype = None

        # Get lang
        if lang:
            if datatype:
                raise TypeError(
                    "A literal can only have one of `lang` or `datatype`."
                )
            string.lang = str(lang)

        # Get datatype
        elif datatype in cls.datatypes:
            string.datatype = cls.datatypes[datatype][0]
        elif datatype:
            # Create canonical representation of value for
            # given datatype
            val = None
            for typ, names in cls.datatypes.items():
                for name in names:
                    if name == datatype:
                        try:
                            val = typ(value)
                            break
                        except:  # pylint: disable=bare-except
                            pass  # nosec
                    if val:
                        break
            if val is not None:
                # Re-initialize the value anew, similarly to what is done in
                # the first line of this method.
                string = super().__new__(cls, val)
                string.lang = None

            string.datatype = datatype

        # Infer datatype from value
        elif isinstance(value, Literal):
            string.lang = value.lang
            string.datatype = value.datatype
        elif isinstance(value, str):
            string.datatype = None
        elif isinstance(value, bool):
            string.datatype = XSD.boolean
        elif isinstance(value, int):
            string.datatype = XSD.integer
        elif isinstance(value, float):
            string.datatype = XSD.double
        elif isinstance(value, (bytes, bytearray)):
            # Re-initialize the value anew, similarly to what is done in
            # the first line of this method.
            string = super().__new__(cls, value.hex())
            string.lang = None
            string.datatype = XSD.hexBinary
        elif isinstance(value, datetime):
            string.datatype = XSD.dateTime
            # TODO:
            #   - XSD.base64Binary
            #   - XSD.byte, XSD.unsignedByte

        # Some consistency checking
        if (
            string.datatype == XSD.nonPositiveInteger
            and int(value) > 0  # type: ignore[arg-type]
        ):
            raise TypeError(f"not a xsd:nonPositiveInteger: '{string}'")
        if (
            string.datatype == XSD.nonNegativeInteger
            and int(value) < 0  # type: ignore[arg-type]
        ):
            raise TypeError(f"not a xsd:nonNegativeInteger: '{string}'")
        if (
            string.datatype
            in (
                XSD.unsignedInt,
                XSD.unsignedShort,
                XSD.unsignedLong,
                XSD.unsignedByte,
            )
            and int(value) < 0  # type: ignore[arg-type]
        ):
            raise TypeError(f"not an unsigned integer: '{string}'")

        # Check if datatype is known
        if string.datatype and not any(
            string.datatype in types for types in cls.datatypes.values()
        ):
            warnings.warn(
                f"unknown datatype: {string.datatype} - assuming xsd:string"
            )

        return string

    def __hash__(self):
        return hash((str(self), self.lang, self.datatype))

    def __eq__(self, other):
        if not isinstance(other, Literal):
            if isinstance(other, str) and self.lang:
                return str(self) == other
            other = Literal(other)
        return (
            str(self) == str(other)
            and self.lang == other.lang
            and self.datatype == other.datatype
        )

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self) -> str:
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
            value = False if str(self) == "False" else bool(self)
        elif self.datatype in self.datatypes[int]:
            value = int(self)
        elif self.datatype in self.datatypes[float]:
            value = float(self)
        elif self.datatype == XSD.dateTime:
            value = datetime.fromisoformat(self)

        return value

    def n3(self) -> str:  # pylint: disable=invalid-name
        """Returns a representation in n3 format."""
        if self.lang:
            return f'"{self}"@{self.lang}'
        if self.datatype:
            return f'"{self}"^^{self.datatype}'
        return f"{self}"
