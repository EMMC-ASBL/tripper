"""Test rdflib backend.

Most of the rdflib backend is already tested in tests/test_triplestore.py.
"""

# pylint: disable=invalid-name


def test_rdflib_backend():
    """Test rdflib backend."""
    import pytest

    pytest.importorskip("rdflib")

    from tripper import RDFS, Literal, Triplestore

    ts = Triplestore("rdflib")
    EX = ts.bind("", "http://ex#")

    # Test for issue #162: Literals are lost when accessing triples with rdflib
    ts.parse(
        format="turtle",
        data=(
            "<http://ex#s> <http://ex#p> "
            '"abc"^^<http://www.w3.org/2001/XMLSchema#string> .'
        ),
    )
    assert list(ts.triples()) == [
        (
            "http://ex#s",
            "http://ex#p",
            Literal("abc", datatype="http://www.w3.org/2001/XMLSchema#string"),
        )
    ]

    # Test for bnode
    ts.add_triples([("_:bn1", RDFS.subClassOf, EX.s)])
    assert ts.value(predicate=RDFS.subClassOf, object=EX.s) == "_:bn1"

    assert ts.prefer_sparql is False
