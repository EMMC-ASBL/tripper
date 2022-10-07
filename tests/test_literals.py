"""Test RDF literals."""


def test_string() -> None:
    """Test creating a string literal."""
    from tripper.triplestore import Literal

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
    from tripper.triplestore import Literal

    literal = Literal("Hello world!", lang="en")
    assert literal.lang == "en"
    assert literal.datatype is None
    assert literal.value == "Hello world!"
    assert literal.n3() == '"Hello world!"@en'


def test_en() -> None:
    """Test creating a string literal through `en()`."""
    from tripper.triplestore import en

    literal = en("Hello world!")
    assert literal.n3() == '"Hello world!"@en'


def test_integer() -> None:
    """Test creating an integer literal."""
    from tripper.triplestore import XSD, Literal

    literal = Literal(42)
    assert literal.lang is None
    assert literal.datatype == XSD.integer
    assert literal.value == 42
    assert literal.n3() == f'"42"^^{XSD.integer}'


def test_float_through_datatype() -> None:
    """Test creating a float literal from an int through datatype."""
    from tripper.triplestore import XSD, Literal

    literal = Literal(42, datatype=float)
    assert literal.lang is None
    assert literal.datatype == XSD.double
    assert literal.value == 42.0
    assert literal.n3() == f'"42"^^{XSD.double}'
