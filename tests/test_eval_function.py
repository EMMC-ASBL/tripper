"""Test Triplestore.eval_function()"""

import pytest

from tripper import Triplestore

pytest.importorskip("rdflib")


def func(a, b):
    """Returns the sum of `a` and `b`."""
    # pylint: disable=invalid-name
    return a + b


ts = Triplestore(backend="rdflib")
EX = ts.bind("ex", "http://example.com/ex#")

# Test to add function in current scope
iri = ts.add_function(
    func,
    expects=[EX.arg1, EX.arg2],
    returns=EX.sum,
    standard="emmo",
)
assert ts.eval_function(func_iri=iri, args=(2, 3)) == 5


# Test to add a function from the standard library. The hashlib module
# is not expected to be imported in the current scope
iri2 = ts.add_function(
    EX.shake256,
    expects=[EX.Bytes],
    returns=EX.ShakeVar,
    func_name="shake_256",
    module_name="hashlib",
)
shakevar = ts.eval_function(iri2, (b"a",))
assert shakevar.hexdigest(4) == "867e2cb0"


# Test to add a function from a pypi package.
iri3 = ts.add_function(
    EX.UFloat,
    expects=[EX.Uncertainty],
    returns=EX.UUID,
    func_name="ufloat",
    module_name="uncertainties",
    # package_name="uncertainties",
    pypi_package_name="uncertainties==3.1.7",
)
val = ts.eval_function(iri3, args=(1, 0.1))
assert val.n == 1
assert val.s == 0.1
