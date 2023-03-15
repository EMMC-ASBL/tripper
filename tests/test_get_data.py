"""Test Triplestore.get_data() and related methods."""
# pylint: disable=unused-argument,invalid-name
import numpy as np

from tripper import Literal, Triplestore
from tripper.mappings import Value


def get_lengths(iri, configurations, triplestore):
    """Return data from a data source. Here a length with unit."""
    return Value([1, 7, 2, 3], unit="m")


def get_string(iri, configurations, triplestore):
    """Return data from a data source. Here a string."""
    return "a string"


def get_number(iri, configurations, triplestore):
    """Return data from a data source. Here a number."""
    return 2.78


def xcoords(iri, configurations, triplestore):
    """Return data from a data source. Here a list of lengths."""
    return Value(value=[0, 2, 4, 6, 8, 10], unit="m")


def ycoords(iri, configurations, triplestore):
    """Return data from a data source. Here a list of voltages."""
    return Value(value=[0, 4, 16, 36, 64, 100], unit="V")


ts = Triplestore(backend="rdflib")
EX = ts.bind("ex", "http://example.com/onto#")

string_iri = ts.add_data(Literal("string value"), EX.Description)
number_iri = ts.add_data(Literal(3.14), EX.WellKnownNumber)
length_iri = ts.add_data(get_lengths, EX.Length)
string2_iri = ts.add_data(get_string, EX.String)
xcoords_iri = ts.add_data(xcoords)
ycoords_iri = ts.add_data(ycoords)

assert ts.get_value(string_iri) == "string value"
assert ts.get_value(number_iri) == 3.14
assert np.allclose(ts.get_value(length_iri).m, [1, 7, 2, 3])
assert ts.get_value(string2_iri) == "a string"
assert np.allclose(ts.get_value(xcoords_iri).m, [0, 2, 4, 6, 8, 10])
assert np.allclose(ts.get_value(xcoords_iri, magnitude=True), [0, 2, 4, 6, 8, 10])
assert np.allclose(ts.get_value(xcoords_iri, unit="dm"), [0, 20, 40, 60, 80, 100])
assert np.allclose(ts.get_value(ycoords_iri).m, [0, 4, 16, 36, 64, 100])


# Test get_value() via mappings
ts.map(EX.indv, EX.Description)
assert ts.get_value(EX.indv) == "string value"

ts.map(EX.indv2, EX.WellKnownNumber)
assert ts.get_value(EX.indv2) == 3.14

ts.map(EX.indv3, EX.Length)
q3 = ts.get_value(EX.indv3)
assert np.allclose(q3.m, [1, 7, 2, 3])
assert np.allclose(q3.m_as("dm"), [10, 70, 20, 30])

ts.map(EX.indv4, EX.String)
assert ts.get_value(EX.indv4) == "a string"


# Test interpolation source
ts.add_interpolation_source(xcoords_iri, ycoords_iri, EX.Length, EX.Voltage)
ts.map(EX.indv5, EX.Voltage)
assert np.allclose(ts.get_value(EX.indv5).m, [2, 50, 4, 10])
