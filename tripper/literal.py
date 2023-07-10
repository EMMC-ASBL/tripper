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
        string = super().__new__(cls, value)
        if lang:
            if datatype:
                raise TypeError(
                    "A literal can only have one of `lang` or `datatype`."
                )
            string.lang = str(lang)
            string.datatype = None
        else:
            string.lang = None
            if datatype:
                string.datatype = cls.datatypes.get(datatype, (datatype,))[0]
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
            else:
                string.datatype = None
        return string

    # These two methods are commeted out for now because they cause
    # the DLite example/mapping/mappingfunc.py example to fail.
    #
    # It seems that these methods cause the datatype be changed to
    # an "h" in some relations added by the add_function() method.

    # def __hash__(self):
    #     return hash((str(self), self.lang, self.datatype))

    # def __eq__(self, other):
    #     if isinstance(other, Literal):
    #         return (
    #             str(self) == str(other)
    #             and self.lang == other.lang
    #             and self.datatype == other.datatype
    #         )
    #     return str(self) == str(other)

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
            value = False if self == "False" else bool(self)
        elif self.datatype in self.datatypes[int]:
            value = int(self)
        elif self.datatype in self.datatypes[float]:
            value = float(self)
        elif self.datatype == XSD.hexBinary:
            value = self.encode()
        elif self.datatype == XSD.dateTime:
            value = datetime.fromisoformat(self)
        elif self.datatype and self.datatype not in self.datatypes[str]:
            warnings.warn(
                f"unknown datatype: {self.datatype} - assuming string"
            )

        return value

    def n3(self) -> str:  # pylint: disable=invalid-name
        """Returns a representation in n3 format."""
        if self.lang:
            return f'"{self}"@{self.lang}'
        if self.datatype:
            return f'"{self}"^^{self.datatype}'
        return f'"{self}"'
