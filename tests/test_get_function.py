"""Test Triplestore.get_function()"""
from tripper import Triplestore


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
f = ts.get_function(iri)
assert f(2, 3) == 5


# Try to add the hashlib.shake_256() function.  Note that hashlib is
# not in the current scope.
iri2 = ts.add_function(
    EX.shape256,
    expects=[EX.Bytes],
    returns=EX.ShakeVar,
    func_name="shake_256",
    module_name="hashlib",
)
shake = ts.get_function(iri2)
shakevar = shake(b"a")
assert shakevar.hexdigest(4) == "867e2cb0"
