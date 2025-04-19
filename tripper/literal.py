"""Literal RDF values.

Literals may be used as objects in RDF triples to provide a value to a
resource.

See also https://www.w3.org/TR/rdf11-concepts/#section-Graph-Literal

"""

import json
import warnings
from datetime import datetime
from typing import TYPE_CHECKING

from tripper.errors import UnknownDatatypeWarning
from tripper.namespace import RDF, RDFS, XSD

if TYPE_CHECKING:  # pragma: no cover
    from typing import Optional, Union

try:
    from pint import Quantity
except ModuleNotFoundError:
    Quantity = None

SIQuantityDatatype = (
    "https://w3id.org/emmo#EMMO_799c067b_083f_4365_9452_1f1433b03676"
)


class Literal(str):
    """A literal RDF value.

    Arguments:
        value (Union[datetime, bytes, bytearray, bool, int, float,
            str, None, dict, list]): The literal value. Can be
            given as a string or a Python object.
        lang (Optional[str]): A standard language code, like "en",
            "no", etc.  Implies that the `value` is a language-tagged
            string.
        datatype (Optional[str, type]): The datatype of this literal.
            Can be given either as a string with the datatype IRI (ex:
            `"http://www.w3.org/2001/XMLSchema#integer"`) or as a
            Python type (ex: `int`).  If not given, the datatype is
            inferred from `value`.  Should not be combined with
            `lang`.

    Examples:

        ```python
        >>> from tripper import XSD, Literal

        # Inferring the data type
        >>> l1 = Literal(42)
        >>> l1
        Literal('42', datatype='http://www.w3.org/2001/XMLSchema#integer')

        >>> l1.value
        42

        # String values with no datatype are assumed to be strings
        >>> l2 = Literal("42")
        >>> l2.value
        '42'

        # Explicit providing the datatype
        >>> l3 = Literal("42", datatype=XSD.integer)
        >>> l3
        Literal('42', datatype='http://www.w3.org/2001/XMLSchema#integer')

        >>> l3.value
        42

        # Localised or language-tagged string literal
        >>> Literal("Hello world", lang="en")
        Literal('Hello world', lang='en')

        # Dicts, lists and None are assumed to be of type rdf:JSON
        >>> l4 = Literal({"name": "Jon Doe"})
        >>> l4.datatype
        'http://www.w3.org/1999/02/22-rdf-syntax-ns#JSON'

        >>> l4.value
        {'name': 'Jon Doe'}

        # Literal of custom datatype (`value` must be a string)
        # This will issue an `UnknownDatatypeWarning` which we ignore...
        >>> import warnings
        >>> from tripper.errors import UnknownDatatypeWarning
        >>> with warnings.catch_warnings():
        ...     warnings.filterwarnings(
        ...         action="ignore", category=UnknownDatatypeWarning,
        ...     )
        ...     Literal("a value", datatype="http://example.com/onto#MyType")
        Literal('a value', datatype='http://example.com/onto#MyType')

        ```

    """

    # Note that the order of datatypes matters - it is used by
    # utils.parse_literal() when inferring the datatype of a literal.
    datatypes = {
        datetime: (XSD.dateTime,),
        bytes: (XSD.hexBinary, XSD.base64Binary),
        bytearray: (XSD.hexBinary, XSD.base64Binary),
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
            RDFS.Literal,
            RDF.PlainLiteral,
            RDF.HTML,
            RDF.JSON,
            RDF.XMLLiteral,
            RDF.langString,
            XSD.NCName,
            XSD.NMTOKEN,
            XSD.Name,
            XSD.anyURI,
            XSD.language,
            XSD.normalizedString,
            XSD.token,
        ),
        list: (RDF.JSON,),
        dict: (RDF.JSON,),
        None.__class__: (RDF.JSON,),
    }
    if Quantity:
        datatypes[Quantity] = (SIQuantityDatatype,)

    lang: "Union[str, None]"
    datatype: "Union[str, None]"

    def __new__(
        cls,
        value: (
            "Union[datetime, bytes, bytearray, bool, int, float, str, None, "
            "dict, list]"
        ),
        lang: "Optional[str]" = None,
        datatype: "Optional[Union[str, type]]" = None,
    ):
        # pylint: disable=too-many-branches,too-many-statements
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
            string.datatype = cls.datatypes[datatype][0]  # type: ignore
        elif datatype == RDF.JSON:
            if isinstance(value, str):
                # Raises an exception if `value` is not a valid JSON string
                json.loads(value)
            else:
                value = json.dumps(value)
            string = super().__new__(cls, value)
            string.lang = None
            string.datatype = RDF.JSON
        elif datatype == SIQuantityDatatype:
            if Quantity and isinstance(value, Quantity):
                value = f"{value:~P}"
            string = super().__new__(cls, value)
            string.lang = None
            string.datatype = SIQuantityDatatype
        elif datatype:
            assert isinstance(datatype, str)  # nosec
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
        elif value is None or isinstance(value, (dict, list)):
            string = super().__new__(cls, json.dumps(value))
            string.lang = None
            string.datatype = RDF.JSON
        elif Quantity and isinstance(value, Quantity):
            string = super().__new__(cls, f"{value:~P}")
            string.lang = None
            string.datatype = SIQuantityDatatype

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
                f"unknown datatype: {string.datatype} - assuming xsd:string",
                category=UnknownDatatypeWarning,
            )

        return string

    def __hash__(self):
        return hash((str(self), self.lang, self.datatype))

    def __eq__(self, other):  # pylint: disable=too-many-return-statements
        if not isinstance(other, Literal):
            if isinstance(other, str) and (
                self.lang or self.datatype in self.datatypes[str]
            ):
                return str(self) == other
            other = Literal(other)
        if str(self) != str(other):
            return False
        if self.lang and other.lang and self.lang != other.lang:
            return False
        if (
            self.datatype
            and other.datatype
            and self.datatype != other.datatype
        ):
            return False
        strings = set(self.datatypes[str] + (None,))
        if self.datatype is None and other.datatype not in strings:
            return False
        if other.datatype is None and self.datatype not in strings:
            return False
        return True

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
        if self.datatype == XSD.boolean:
            value = False if str(self) == "False" else bool(self)
        elif self.datatype in self.datatypes[int]:
            value = int(self)
        elif self.datatype in self.datatypes[float]:
            value = float(self)
        elif self.datatype == XSD.dateTime:
            value = datetime.fromisoformat(self)
        elif self.datatype == RDF.JSON:
            value = json.loads(str(self))
        elif self.datatype == SIQuantityDatatype:
            if Quantity:
                # pylint: disable=import-outside-toplevel,cyclic-import
                from tripper.units import get_ureg

                ureg = get_ureg()
                value = ureg.Quantity(self)
            else:
                warnings.warn(
                    "pint is needed to convert emmo:SIQuantityDatatype to "
                    "a quantity"
                )
                value = str(self)
        else:
            value = str(self)

        return value

    def n3(self) -> str:  # pylint: disable=invalid-name
        """Returns a representation in n3 format."""

        form = self.replace("\\", r"\\").replace('"', r"\"")

        if self.lang:
            return f'"{form}"@{self.lang}'
        if self.datatype:
            return f'"{form}"^^<{self.datatype}>'
        return f'"{form}"'
