"""Test RDF literals."""


def test_string() -> None:
    """Test creating a string literal."""
    from tripper import Literal

    literal = Literal("Hello world!")
    assert literal == "Hello world!"
    assert isinstance(literal, str)
    assert literal.lang is None
    assert literal.datatype is None
    assert literal.to_python() == "Hello world!"
    assert literal.value == "Hello world!"
    assert literal.n3() == '"Hello world!"'


def test_string_lang() -> None:
    """Test creating a string literal with a set language."""
    from tripper import Literal

    literal = Literal("Hello world!", lang="en")
    assert literal.lang == "en"
    assert literal.datatype is None
    assert literal.value == "Hello world!"
    assert literal.n3() == '"Hello world!"@en'


def test_en() -> None:
    """Test creating a string literal through `en()`."""
    from tripper import en

    literal = en("Hello world!")
    assert literal.n3() == '"Hello world!"@en'


def test_integer() -> None:
    """Test creating an integer literal."""
    from tripper import XSD, Literal

    literal = Literal(42)
    assert literal.lang is None
    assert literal.datatype == XSD.integer
    assert literal.value == 42
    assert literal.n3() == f'"42"^^{XSD.integer}'


def test_float_through_datatype() -> None:
    """Test creating a float literal from an int through datatype."""
    from tripper import XSD, Literal

    literal = Literal(42, datatype=float)
    assert literal.lang is None
    assert literal.datatype == XSD.double
    assert literal.value == 42.0
    assert literal.n3() == f'"42"^^{XSD.double}'


def test_split_iri() -> None:
    """Test parse n3-encoded literal value."""
    from tripper import DCTERMS, RDFS, split_iri

    namespace, name = split_iri(DCTERMS.prefLabel)
    assert namespace == str(DCTERMS)
    assert name == "prefLabel"

    namespace, name = split_iri(RDFS.subClassOf)
    assert namespace == str(RDFS)
    assert name == "subClassOf"


def test_parse_literal() -> None:
    """Test parse n3-encoded literal value."""
    from tripper import XSD, Literal, parse_literal

    value, lang, datatype = parse_literal(Literal("abc").n3())
    assert value == "abc"
    assert lang is None
    assert datatype == XSD.string

    value, lang, datatype = parse_literal(Literal("abc", lang="en").n3())
    assert value == "abc"
    assert lang == "en"
    assert datatype is None

    value, lang, datatype = parse_literal(Literal(3).n3())
    assert value == 3
    assert lang is None
    assert datatype == XSD.integer

    value, lang, datatype = parse_literal(Literal(3.14).n3())
    assert value == 3.14
    assert lang is None
    assert datatype == XSD.double

    value, lang, datatype = parse_literal(Literal(True).n3())
    assert value is True
    assert lang is None
    assert datatype == XSD.boolean

    value, lang, datatype = parse_literal("3")
    assert value == 3
    assert lang is None
    assert datatype == XSD.integer

    value, lang, datatype = parse_literal("3.14")
    assert value == 3.14
    assert lang is None
    assert datatype == XSD.double
