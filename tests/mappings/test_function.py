"""Test mapping function."""


def test_mapping():
    """Test mapping function.

    We have two data sources:
      - literal number 3.2 mapped to ex:A
      - vector mapped to ex:B

    We also have two mapping functions; first() and sum()
      - first(): ex:B[0] -> ex:C
      - sum(): ex:A + ex:C -> ex:D

    The test asks for the value of an individual of ex:D

    Uses rdflib as backend
    """
    # pylint: disable=unused-argument,invalid-name
    import pytest

    pytest.importorskip("rdflib")
    from tripper import Literal, Tripper

    tp = Tripper(backend="rdflib")
    EX = tp.bind("ex", "http://example.com/onto#")

    def first(vector):
        """Return first element of the vector."""
        return vector[0]

    def add(a, b):
        """Return the sum of `a` and `b`."""
        return a + b

    def vector(iri, configurations, triplestore):
        """Return a vector."""
        return [0.5, 1.2, 3.4, 6.6]

    tp.add_data(Literal(3.2), EX.A)
    tp.add_data(vector, EX.B)

    tp.add_function(first, expects=EX.B, returns=EX.C)
    tp.add_function(add, expects=(EX.A, EX.C), returns=EX.D)

    tp.map(EX.indv, EX.D)
    assert tp.get_value(EX.indv) == 3.7
