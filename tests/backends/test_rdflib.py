"""Test rdflib backend.

Most of the rdflib backend is already tested in tests/test_triplestore.py.
"""

import pytest

from tripper import Literal, Triplestore

rdflib = pytest.importorskip("rdflib")


# Test for issue #162: Literals are lost when listing triples with rdflib
ts = Triplestore("rdflib")
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
