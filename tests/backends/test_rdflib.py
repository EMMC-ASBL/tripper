"""Test rdflib backend.

Most of the rdflib backend is already tested in tests/test_triplestore.py.
"""

import pytest

pytest.importorskip("rdflib")

# pylint: disable=invalid-name


def test_rdflib_backend():
    """Test rdflib backend."""

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


def test_rdflib_triplestore_url():
    """Test loading an rdflib triplestore using the `triplestore_url`
    argument."""
    from pathlib import Path

    from tripper import FOAF, RDF, Namespace, Triplestore

    testdir = Path(__file__).resolve().parent.parent
    inputdir = testdir / "input"

    ts = Triplestore("rdflib", triplestore_url=inputdir / "testkb.ttl")
    assert "ex" in ts.namespaces
    EX = Namespace(ts.namespaces["ex"])
    assert ts.has(EX.JohnDow, RDF.type, FOAF.Person)
