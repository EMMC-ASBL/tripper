"""Test RDF literals."""
# pylint: disable=no-member
from triplestore import XSD, Literal, en

l1 = Literal("Hello world!")
assert l1 == "Hello world!"
assert isinstance(l1, str)
assert l1.lang is None
assert l1.datatype is None
assert l1.to_python() == "Hello world!"
assert l1.value == "Hello world!"
assert l1.n3() == '"Hello world!"'

l2 = Literal("Hello world!", lang="en")
assert l2.lang == "en"
assert l2.datatype is None
assert l2.value == "Hello world!"
assert l2.n3() == '"Hello world!"@en'

l3 = en("Hello world!")
assert l3.n3() == '"Hello world!"@en'

l4 = Literal(42)
assert l4.lang is None
assert l4.datatype == XSD.integer
assert l4.value == 42
assert l4.n3() == f'"42"^^{XSD.integer}'

l5 = Literal(42, datatype=float)
assert l5.lang is None
assert l5.datatype == XSD.double
assert l5.value == 42.0
assert l5.n3() == f'"42"^^{XSD.double}'
