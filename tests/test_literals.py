"""Test RDF literals."""

# pylint: disable=invalid-name,too-many-statements


def test_untyped() -> None:
    """Test creating a untyped literal."""
    from tripper.literal import Literal

    literal = Literal("Hello world!")
    assert literal == "Hello world!"
    assert Literal(literal) == "Hello world!"
    assert isinstance(literal, str)
    assert literal.lang is None
    assert literal.datatype is None
    assert literal.to_python() == "Hello world!"
    assert literal.value == "Hello world!"
    assert literal.n3() == "Hello world!"


def test_string() -> None:
    """Test creating a string literal."""
    from tripper.literal import XSD, Literal

    literal = Literal("Hello world!", datatype=XSD.string)
    assert literal == Literal("Hello world!", datatype=XSD.string)
    assert Literal(literal) == Literal("Hello world!", datatype=XSD.string)
    assert isinstance(literal, str)
    assert literal.lang is None
    assert literal.datatype == XSD.string
    assert literal.to_python() == "Hello world!"
    assert literal.value == "Hello world!"
    assert literal.n3() == f'"Hello world!"^^{XSD.string}'
    assert literal != "Hello world!"


def test_string_lang() -> None:
    """Test creating a string literal with a set language."""
    from tripper.literal import Literal

    literal = Literal("Hello world!", lang="en")
    assert literal == Literal("Hello world!", lang="en")
    assert Literal(literal) == Literal("Hello world!", lang="en")
    assert literal.lang == "en"
    assert literal.datatype is None
    assert literal.value == "Hello world!"
    assert literal.n3() == '"Hello world!"@en'


def test_cannot_combine_datatype_and_lang() -> None:
    """Test that combining datatype and lang raises TypeError."""
    import pytest

    from tripper import XSD, Literal

    with pytest.raises(TypeError):
        Literal("1", datatype=XSD.string, lang="en")


def test_en() -> None:
    """Test creating a string literal through `en()`."""
    from tripper.utils import en

    literal = en("Hello world!")
    assert literal.n3() == '"Hello world!"@en'


def test_integer() -> None:
    """Test creating an integer literal."""
    import pytest

    from tripper import XSD, Literal

    literal = Literal(42)
    assert literal == Literal(42)
    assert Literal(literal) == Literal(42)
    assert literal.lang is None
    assert literal.datatype == XSD.integer
    assert literal.value == 42
    assert literal.n3() == f'"42"^^{XSD.integer}'

    with pytest.raises(TypeError):
        Literal(42, datatype=XSD.nonPositiveInteger)

    with pytest.raises(TypeError):
        Literal(-42, datatype=XSD.nonNegativeInteger)

    with pytest.raises(TypeError):
        Literal(-42, datatype=XSD.unsignedInt)


def test_hexbinary() -> None:
    """Test creating hexbinary literal."""
    from tripper import XSD, Literal

    literal = Literal(b"hi")
    assert literal.lang is None
    assert literal.datatype == XSD.hexBinary
    assert literal.value == "6869"
    assert literal.n3() == f'"6869"^^{XSD.hexBinary}'

    literal = Literal("1f", datatype=XSD.hexBinary)
    assert literal.lang is None
    assert literal.datatype == XSD.hexBinary
    assert literal.value == "1f"
    assert literal.n3() == f'"1f"^^{XSD.hexBinary}'


def test_float_through_datatype() -> None:
    """Test creating a float literal from an int through datatype."""
    from tripper import XSD, Literal

    literal = Literal(42, datatype=float)
    assert literal.lang is None
    assert literal.datatype == XSD.double
    assert literal.value == 42.0
    assert literal.n3() == f'"42"^^{XSD.double}'


def test_repr() -> None:
    """Test repr formatting."""
    from tripper import Literal

    literal = Literal(42, datatype=float)
    assert repr(literal) == (
        "Literal('42', datatype='http://www.w3.org/2001/XMLSchema#double')"
    )


def test_split_iri() -> None:
    """Test parse n3-encoded literal value."""
    from tripper import DCTERMS, RDFS
    from tripper.utils import split_iri

    namespace, name = split_iri(DCTERMS.prefLabel)
    assert namespace == str(DCTERMS)
    assert name == "prefLabel"

    namespace, name = split_iri(RDFS.subClassOf)
    assert namespace == str(RDFS)
    assert name == "subClassOf"


def test_parse_literal() -> None:
    """Test parse n3-encoded literal value."""
    from datetime import datetime

    import pytest

    from tripper import RDF, XSD, Literal
    from tripper.utils import parse_literal

    literal = parse_literal(Literal("abc").n3())
    assert literal.value == "abc"
    assert literal.lang is None
    assert literal.datatype == XSD.string

    literal = parse_literal(Literal("abc", lang="en").n3())
    assert literal.value == "abc"
    assert literal.lang == "en"
    assert literal.datatype is None

    literal = parse_literal(Literal(3).n3())
    assert literal.value == 3
    assert literal.lang is None
    assert literal.datatype == XSD.integer

    literal = parse_literal(Literal(3.14).n3())
    assert literal.value == 3.14
    assert literal.lang is None
    assert literal.datatype == XSD.double

    literal = parse_literal(Literal(True).n3())
    assert literal.value is True
    assert literal.lang is None
    assert literal.datatype == XSD.boolean

    literal = parse_literal(Literal(False).n3())
    assert literal.value is False
    assert literal.lang is None
    assert literal.datatype == XSD.boolean

    dt = datetime(2022, 10, 23)
    literal = parse_literal(Literal(dt).n3())
    assert literal.value == dt
    assert literal.lang is None
    assert literal.datatype == XSD.dateTime

    literal = parse_literal(dt)
    assert literal.value == dt
    assert literal.lang is None
    assert literal.datatype == XSD.dateTime

    literal = parse_literal("abc")
    assert literal.value == "abc"
    assert literal.lang is None
    assert literal.datatype == XSD.string

    literal = parse_literal("3")
    assert literal.value == 3
    assert literal.lang is None
    assert literal.datatype == XSD.integer

    literal = parse_literal("3.14")
    assert literal.value == 3.14
    assert literal.lang is None
    assert literal.datatype == XSD.double

    literal = parse_literal(False)
    assert literal.value is False
    assert literal.lang is None
    assert literal.datatype == XSD.boolean

    literal = parse_literal(f'"text"^^{RDF.HTML}')
    assert literal.value == "text"
    assert literal.lang is None
    assert literal.datatype == RDF.HTML

    literal = parse_literal(f'"text"^^<{RDF.HTML}>')
    assert literal.value == "text"
    assert literal.lang is None
    assert literal.datatype == RDF.HTML

    with pytest.warns(UserWarning, match="unknown datatype"):
        literal = parse_literal('"value"^^http://example.com/vocab#mytype')
    assert literal.value == "value"
    assert literal.lang is None
    assert literal.datatype == "http://example.com/vocab#mytype"


def test_equality() -> None:
    """Test equality."""
    from tripper import RDF, XSD, Literal

    assert Literal("text") == "text"
    assert Literal("text", lang="en") == "text"
    assert Literal("text", lang="dk") == "text"
    assert Literal("text", lang="en") != Literal("text", lang="dk")
    assert Literal("text") == "text"
    assert Literal("text") != "text2"
    assert Literal("text", datatype=XSD.string) != "text"
    assert Literal("text", datatype=RDF.HTML) != "text"
    assert Literal(1) == 1
    assert Literal(1) != 1.0
    assert Literal(1) != "1"
    assert Literal(1, datatype=XSD.double) == 1.0
    assert Literal("1", datatype=XSD.double) == 1.0
    assert Literal("1.", datatype=XSD.double) == 1.0
    assert Literal(1.0) == 1.0
    assert Literal(1.0) != 1
    assert Literal(True) == True  # pylint: disable=singleton-comparison
    assert Literal(True) != "True"

    # Newer versions of Python also allow reverting equality statements
    assert 1.0 == Literal(1, datatype=XSD.double)
