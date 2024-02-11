"""Test custom plugin."""

from tripper import Triplestore

# Test relative import
ts = Triplestore(backend="backends.dummy", package="backends")
assert list(ts.triples()) == [
    ("a", "b", "c"),
    ("d", "e", "f"),
    ("g", "h", "i"),
]
