"""Test custom backend."""

# pylint: disable=import-outside-toplevel


def test_custom_backend():
    """Test custom backend."""
    from tripper import Triplestore

    # Test relative import
    ts = Triplestore(backend="backends.dummy", package="backends")
    assert list(ts.triples()) == [
        ("a", "b", "c"),
        ("d", "e", "f"),
        ("g", "h", "i"),
    ]
