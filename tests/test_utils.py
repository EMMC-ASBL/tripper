"""Test utils"""
# pylint: disable=invalid-name
import dlite
import pytest

from tripper import DCTERMS, RDFS, XSD, Literal
from tripper.utils import (
    en,
    function_id,
    infer_iri,
    parse_literal,
    parse_object,
    split_iri,
)

# Test infer_iri()
assert infer_iri(RDFS.subClassOf) == RDFS.subClassOf

coll = dlite.Collection()
assert infer_iri(coll.meta) == coll.meta.uri
assert infer_iri(coll) == coll.uuid

# Test split_iri()
rdfs = str(RDFS)
assert split_iri(RDFS.subClassOf) == (rdfs, "subClassOf")
assert split_iri(rdfs) == (rdfs, "")
dcterms = str(DCTERMS)
assert split_iri(DCTERMS.author) == (dcterms, "author")
assert split_iri(dcterms) == (dcterms, "")
with pytest.raises(TypeError):
    split_iri(3.14)
with pytest.raises(ValueError):
    split_iri("abc")


# Test function_id()
def f():
    """Function."""
    return 0


def g():
    """Function."""
    return 0


def h():
    """Function."""
    return 1


fid1 = function_id(f)
fid2 = function_id(f)
assert fid2 == fid1
fid3 = function_id(g)
assert fid3 != fid1
fid4 = function_id(h)
assert fid4 != fid1
assert fid4 != fid3


# Test en()
assert en("abc") == Literal("abc", lang="en")

# test parse_literal()
assert parse_literal("abc") == Literal("abc", datatype=XSD.string)
assert parse_literal(True) == Literal("True", datatype=XSD.boolean)
assert parse_literal(1) == Literal("1", datatype=XSD.inteter)
assert parse_literal(3.14) == Literal("3.14", datatype=XSD.double)
assert parse_literal(f'"3.14"^^{XSD.double}') == Literal("3.14", datatype=XSD.double)


# test parse_object()
assert parse_object("True") == Literal("True", datatype=XSD.boolean)
assert parse_object("False") == Literal("False", datatype=XSD.boolean)
assert parse_object("true") == Literal("true", datatype=XSD.string)
assert parse_object("0") == Literal("0", datatype=XSD.integer)
assert parse_object("1") == Literal("1", datatype=XSD.integer)
assert parse_object("-1") == Literal("-1", datatype=XSD.integer)
assert parse_object("42") == Literal("42", datatype=XSD.integer)
assert parse_object("3.14") == Literal("3.14", datatype=XSD.double)
assert parse_object(".1") == Literal(".1", datatype=XSD.double)
assert parse_object("1.") == Literal("1.", datatype=XSD.double)
assert parse_object("1e10") == Literal("1e10", datatype=XSD.double)
assert parse_object("1E10") == Literal("1E10", datatype=XSD.double)
assert parse_object("1e+10") == Literal("1e+10", datatype=XSD.double)
assert parse_object("1e-10") == Literal("1e-10", datatype=XSD.double)
assert parse_object(".1e10") == Literal(".1e10", datatype=XSD.double)
assert parse_object("1.e10") == Literal("1.e10", datatype=XSD.double)
assert parse_object("2022-12-01") == Literal("2022-12-01", datatype=XSD.dateTime)
assert parse_object("2022-12-01 12:30") == Literal(
    "2022-12-01 12:30", datatype=XSD.dateTime
)
assert parse_object("2022-12-01 12:30:30") == Literal(
    "2022-12-01 12:30:30", datatype=XSD.dateTime
)
assert parse_object("2022-12-01T12:30:30") == Literal(
    "2022-12-01T12:30:30", datatype=XSD.dateTime
)
assert parse_object("2022-12-01 12:30:30.50") == Literal(
    "2022-12-01 12:30:30.50", datatype=XSD.dateTime
)
assert parse_object("2022-12-01 12:30:30Z") == Literal(
    "2022-12-01 12:30:30Z", datatype=XSD.dateTime
)
assert parse_object("2022-12-01 12:30:30+01:00") == Literal(
    "2022-12-01 12:30:30+01:00", datatype=XSD.dateTime
)
assert parse_object("abc") == Literal("abc", datatype=XSD.string)
assert parse_object('"abc"@en') == Literal("abc", lang="en")
assert parse_object(str(XSD)) == str(XSD)
assert parse_object(XSD.int) == XSD.int
assert parse_object(f'"42"^^{XSD.integer}') == Literal("42", datatype=XSD.integer)
assert parse_object(f'"4.2"^^{XSD.double}') == Literal("4.2", datatype=XSD.double)

# __FIXME__: parse_object() currently fails for the following cases:
# assert parse_object(f'"42"^^{XSD.double}') == Literal("42", datatype=XSD.double)
# assert parse_object(f'"42"^^{XSD.int}') == Literal("42", datatype=XSD.int)
