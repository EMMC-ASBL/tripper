"""Test RDF literals."""

import pytest

# pylint: disable=invalid-name,too-many-statements,import-outside-toplevel


def test_untyped() -> None:
    """Test creating a untyped literal."""
    from tripper.errors import UnknownDatatypeWarning
    from tripper.literal import XSD, Literal

    literal = Literal("Hello world!")
    assert literal == "Hello world!"
    assert Literal(literal) == "Hello world!"
    assert isinstance(literal, str)
    assert literal.lang is None
    assert literal.datatype is None
    assert literal.to_python() == "Hello world!"
    assert literal.value == "Hello world!"
    assert literal.n3() == '"Hello world!"'
    assert literal == Literal("Hello world!", lang="en")

    # Check two things here:
    #   1) that a plain literal compares false to a non-string literal
    #   2) that we get a warning about unknown XSD.ENTITY datatype
    with pytest.warns(UnknownDatatypeWarning, match="^unknown datatype"):
        assert literal != Literal("Hello world!", datatype=XSD.ENTITY)


def test_string() -> None:
    """Test creating a string literal."""
    from tripper.literal import XSD, Literal

    literal = Literal("Hello world!", datatype=XSD.string)
    assert literal == Literal("Hello world!", datatype=XSD.string)
    assert literal == Literal("Hello world!")
    assert literal != Literal("Hello world!", datatype=XSD.token)
    assert literal != Literal(2, datatype=XSD.int)
    assert Literal(literal) == Literal("Hello world!", datatype=XSD.string)
    assert isinstance(literal, str)
    assert literal.lang is None
    assert literal.datatype == XSD.string
    assert literal.to_python() == "Hello world!"
    assert literal.value == "Hello world!"
    assert literal.n3() == f'"Hello world!"^^<{XSD.string}>'
    assert literal == "Hello world!"
    assert literal == Literal("Hello world!")


def test_string_lang() -> None:
    """Test creating a string literal with a set language."""
    from tripper.literal import XSD, Literal

    literal = Literal("Hello world!", lang="en")
    assert literal == Literal("Hello world!", lang="en")
    assert literal != Literal("Hello world!", lang="it")
    assert Literal(literal) == Literal("Hello world!", lang="en")
    assert literal.lang == "en"
    assert literal.datatype is None
    assert literal.value == "Hello world!"
    assert literal.n3() == '"Hello world!"@en'
    assert literal == "Hello world!"

    # Are these wanted behaviour?  What does the RDF 1.1 standard says?
    assert literal == Literal("Hello world!")
    assert literal == Literal("Hello world!", datatype=XSD.string)
    assert literal == Literal("Hello world!", datatype=XSD.token)


def test_cannot_combine_datatype_and_lang() -> None:
    """Test that combining datatype and lang raises TypeError."""
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
    from tripper import XSD, Literal

    literal = Literal(42)
    assert literal == Literal(42)
    assert Literal(literal) == Literal(42)
    assert literal.lang is None
    assert literal.datatype == XSD.integer
    assert literal.value == 42
    assert literal.n3() == f'"42"^^<{XSD.integer}>'

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
    assert literal.n3() == f'"6869"^^<{XSD.hexBinary}>'

    literal = Literal("1f", datatype=XSD.hexBinary)
    assert literal.lang is None
    assert literal.datatype == XSD.hexBinary
    assert literal.value == "1f"
    assert literal.n3() == f'"1f"^^<{XSD.hexBinary}>'


def test_json() -> None:
    """Test creating JSON literal."""
    import json

    from tripper import RDF, Literal

    literal = Literal(None)
    assert literal.value is None
    assert literal.lang is None
    assert literal.datatype == RDF.JSON
    assert literal.n3() == f'"null"^^<{RDF.JSON}>'

    literal = Literal({"a": 1, "b": [2.2, None, True]})
    assert literal.value == {"a": 1, "b": [2.2, None, True]}
    assert literal.lang is None
    assert literal.datatype == RDF.JSON
    assert literal.n3() == (
        r'"{\"a\": 1, \"b\": [2.2, null, true]}"^^' + f"<{RDF.JSON}>"
    )

    literal = Literal(["a", 1, True, {"a": 2.2, "b": None}])
    assert literal.value == ["a", 1, True, {"a": 2.2, "b": None}]
    assert literal.lang is None
    assert literal.datatype == RDF.JSON
    assert literal.n3() == (
        r'"[\"a\", 1, true, {\"a\": 2.2, \"b\": null}]"^^' + f"<{RDF.JSON}>"
    )

    literal = Literal('{"a": 1}', datatype=RDF.JSON)
    assert literal.value == {"a": 1}
    assert literal.lang is None
    assert literal.datatype == RDF.JSON
    assert literal.n3() == (r'"{\"a\": 1}"^^' + f"<{RDF.JSON}>")

    literal = Literal('"a"', datatype=RDF.JSON)
    assert literal.value == "a"
    assert literal.lang is None
    assert literal.datatype == RDF.JSON
    assert literal.n3() == (r'"\"a\""^^' + f"<{RDF.JSON}>")

    with pytest.raises(json.JSONDecodeError):
        literal = Literal("a", datatype=RDF.JSON)


def test_SIQuantityDatatype() -> None:
    """Test pint Quantity."""
    pint = pytest.importorskip("pint")
    from tripper import Literal
    from tripper.literal import SIQuantityDatatype
    from tripper.utils import parse_literal

    q = pint.Quantity("2 m")
    literal = Literal(q)
    assert literal.value == q
    assert literal.lang is None
    assert literal.datatype == SIQuantityDatatype
    assert literal.n3() == f'"2 m"^^<{SIQuantityDatatype}>'

    literal = Literal("2.5 N", datatype=SIQuantityDatatype)
    assert literal.value == pint.Quantity("2.5 newton")
    assert literal.lang is None
    assert literal.datatype == SIQuantityDatatype
    assert literal.n3() == f'"2.5 N"^^<{SIQuantityDatatype}>'

    literal = parse_literal(f'"3.2 m/s²"^^<{SIQuantityDatatype}>')
    assert literal.value == pint.Quantity("3.2 m/s²")
    assert literal.lang is None
    assert literal.datatype == SIQuantityDatatype
    assert literal.n3() == f'"3.2 m/s²"^^<{SIQuantityDatatype}>'

    literal = parse_literal(pint.Quantity("3.2 m/s²"))
    assert literal.value == pint.Quantity("3.2 m/s²")
    assert literal.lang is None
    assert literal.datatype == SIQuantityDatatype
    assert literal.n3() == f'"3.2 m/s²"^^<{SIQuantityDatatype}>'


def test_float_through_datatype() -> None:
    """Test creating a float literal from an int through datatype."""
    from tripper import XSD, Literal

    literal = Literal(42, datatype=float)
    assert literal.lang is None
    assert literal.datatype == XSD.double
    assert literal.value == 42.0
    assert literal.n3() == f'"42"^^<{XSD.double}>'


def test_repr() -> None:
    """Test repr formatting."""
    from tripper import Literal

    literal = Literal(42, datatype=float)
    assert repr(literal) == (
        "Literal('42', datatype='http://www.w3.org/2001/XMLSchema#double')"
    )


def test_n3() -> None:
    """Test n3()."""
    from tripper import RDF, Literal

    s = Literal(42, datatype=float).n3()
    assert s == '"42"^^<http://www.w3.org/2001/XMLSchema#double>'
    s = Literal("a string").n3()
    assert s == '"a string"'
    s = Literal('a string with "embedded" quotes').n3()
    assert s == r'"a string with \"embedded\" quotes"'
    s = Literal(r"a string with \"escaped\" quotes").n3()
    assert s == r'"a string with \\\"escaped\\\" quotes"'
    s = Literal('"json string"', datatype=RDF.JSON).n3()
    assert s == (
        r'"\"json string\""^^<http://www.w3.org/1999/02/22-rdf-syntax-ns#JSON>'
    )
    s = Literal('{"a": 1}', datatype=RDF.JSON).n3()
    assert (
        s == r'"{\"a\": 1}"^^<http://www.w3.org/1999/02/22-rdf-syntax-ns#JSON>'
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

    from tripper import RDF, XSD, Literal
    from tripper.errors import UnknownDatatypeWarning
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

    literal = parse_literal(3)
    assert literal.value == 3
    assert literal.lang is None
    assert literal.datatype == XSD.integer

    literal = parse_literal("3")
    assert literal.value == 3
    assert literal.lang is None
    assert literal.datatype == XSD.integer

    literal = parse_literal(3.14)
    assert literal.value == 3.14
    assert literal.lang is None
    assert literal.datatype == XSD.double

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

    literal = parse_literal(f'"""text"""^^<{RDF.HTML}>')
    assert literal.value == "text"
    assert literal.lang is None
    assert literal.datatype == RDF.HTML

    literal = parse_literal(f'"""["a", 1, 2]"""^^<{RDF.JSON}>')
    assert literal.value == ["a", 1, 2]
    assert literal.lang is None
    assert literal.datatype == RDF.JSON

    with pytest.warns(UnknownDatatypeWarning, match="unknown datatype"):
        literal = parse_literal('"value"^^http://example.com/vocab#mytype')
    assert literal.value == "value"
    assert literal.lang is None
    assert literal.datatype == "http://example.com/vocab#mytype"

    literal = parse_literal({"a": 1, "b": [2.2, None, True]})
    assert literal.value == {"a": 1, "b": [2.2, None, True]}
    assert literal.lang is None
    assert literal.datatype == RDF.JSON

    literal = parse_literal(
        f'"""{{"a": 1, "b": [2.2, null, true]}}"""^^<{RDF.JSON}>'
    )
    assert literal.value == {"a": 1, "b": [2.2, None, True]}
    assert literal.lang is None
    assert literal.datatype == RDF.JSON


def test_rdflib_literal():
    """Test parsing rdflib literals."""
    rdflib = pytest.importorskip("rdflib")
    from tripper import RDF, XSD
    from tripper.utils import parse_literal

    rdflib_literal = rdflib.Literal(1, datatype=rdflib.XSD.integer)
    literal = parse_literal(rdflib_literal)
    assert literal.value == 1
    assert literal.lang is None
    assert literal.datatype == XSD.integer

    rdflib_literal = rdflib.Literal("abc", datatype=rdflib.XSD.string)
    literal = parse_literal(rdflib_literal)
    assert literal.value == "abc"
    assert literal.lang is None
    assert literal.datatype == XSD.string

    rdflib_literal = rdflib.Literal('["a", 1, 2]', datatype=rdflib.RDF.JSON)
    literal = parse_literal(rdflib_literal)
    assert literal.value == ["a", 1, 2]
    assert literal.lang is None
    assert literal.datatype == RDF.JSON


def test_equality() -> None:
    """Test equality."""
    from tripper import RDF, XSD, Literal

    assert Literal("text") == "text"
    assert Literal("text", lang="en") == "text"
    assert Literal("text", lang="dk") == "text"
    assert Literal("text", lang="en") != Literal("text", lang="dk")
    assert Literal("text") == "text"
    assert Literal("text") != "text2"
    assert Literal("text", datatype=XSD.string) == "text"
    assert Literal("text", datatype=RDF.HTML) == "text"
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
