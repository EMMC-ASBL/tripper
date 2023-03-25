"""Test mapping function.

We have two data sources:
  - literal number 3.2 mapped to ex:A
  - vector mapped to ex:B

We also have two mapping functions; first() and sum()
  - first(): ex:B[0] -> ex:C
  - sum(): ex:A + ex:C -> ex:D

The test asks for the value of an individual of ex:D
"""
# pylint: disable=unused-argument,invalid-name
from tripper import Literal, Triplestore

ts = Triplestore(backend="rdflib")
EX = ts.bind("ex", "http://example.com/onto#")


def first(vector):
    """Return first element of the vector."""
    return vector[0]


def add(a, b):
    """Return the sum of `a` and `b`."""
    return a + b


def vector(iri, configurations, triplestore):
    """Return a vector."""
    return [0.5, 1.2, 3.4, 6.6]


ts.add_data(Literal(3.2), EX.A)
ts.add_data(vector, EX.B)

ts.add_function(first, expects=EX.B, returns=EX.C)
ts.add_function(add, expects=(EX.A, EX.C), returns=EX.D)

ts.map(EX.indv, EX.D)
assert ts.get_value(EX.indv) == 3.7
