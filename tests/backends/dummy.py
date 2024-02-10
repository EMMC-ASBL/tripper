"""Dummy tripper backend for testing loading a custom backend."""

# pylint: disable=unused-argument


class DummyStrategy:
    """Dummy strategy."""

    def __init__(self, base_iri=None, **kwargs):
        """Initialise triplestore."""

    def triples(self, triple):
        """Returns a generator over matching triples."""
        return ((s, p, o) for s, p, o in ("abc", "def", "ghi"))

    def add_triples(self, triples):
        """Add a sequence of triples."""

    def remove(self, triple):
        """Remove all matching triples."""
