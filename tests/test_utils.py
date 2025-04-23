"""Test utils"""

# pylint: disable=invalid-name,too-few-public-methods,import-outside-toplevel

import pytest


def test_AttrDict():
    """Test AttrDict."""
    from tripper.utils import AttrDict

    d = AttrDict(a=1, b=2)
    assert d.a == 1

    with pytest.raises(KeyError):
        d.c  # pylint: disable=pointless-statement

    d.c = 3
    assert d.c == 3

    d.get = 4
    assert d["get"] == 4
    assert d.get("get") == 4  # pylint: disable=not-callable

    d2 = AttrDict({"a": "A"})
    assert d2.a == "A"
    assert d2 == {"a": "A"}
    assert repr(d2) == "AttrDict({'a': 'A'})"
    assert "a" in dir(d2)


# if True:
def test_recursive_update():
    """Test recursive_update()."""
    from tripper.utils import AttrDict, recursive_update

    d = {"a": {"b": "bval", "c": "cval"}}
    recursive_update(d, {"a": {"b": "bval"}})
    assert d == {"a": {"b": "bval", "c": "cval"}}

    other = {"a": [1, {"b": 2, "c": [3, 4]}, 5], "d": 6}
    d = {"a": []}
    recursive_update(d, other)
    assert d == other
    assert isinstance(d["a"][1], dict)

    d = {"a": []}
    recursive_update(d, other, cls=AttrDict)
    assert d == other
    assert isinstance(d["a"][1], AttrDict)

    d = AttrDict()
    recursive_update(d, other)
    assert d == other
    assert isinstance(d.a[1], AttrDict)

    d = {"d": 1}
    recursive_update(d, other)
    assert d == {"a": [1, {"b": 2, "c": [3, 4]}, 5], "d": [1, 6]}

    d = {"d": 1}
    recursive_update(d, other, append=False)
    assert d == {"a": [1, {"b": 2, "c": [3, 4]}, 5], "d": 6}

    d = {"a": {"b": 2}}
    recursive_update(d, {"a": [1, {"b": 2}]})
    assert d == {"a": [1, {"b": 2}]}  #

    d = {"a": {"b": 2}}
    recursive_update(d, {"a": [1, {"b": 2}]}, append=False)
    assert d == {"a": [1, {"b": 2}]}

    d = {"a": [1, {"b": 2}]}
    recursive_update(d, {"a": [1, {"b": 2}]})
    assert d == {"a": [1, {"b": 2}]}

    d = {"a": {"b": 2}}
    recursive_update(d, {"a": [1, {"b": 3}]})
    assert d == {"a": [1, {"b": [2, 3]}]}

    d = {"a": {"b": 2}}
    recursive_update(d, {"a": [1, {"b": 3}]}, append=False)
    assert d == {"a": [1, {"b": 3}]}

    d = {"a": "val1"}
    recursive_update(d, {"a": "val1", "b": "val2"})
    assert d == {"a": "val1", "b": "val2"}

    d = {"a": {"b": "val1"}, "c": 1}
    recursive_update(d, {"a": {"b": "val1"}})
    assert d == {"a": {"b": "val1"}, "c": 1}

    d = {"a": {"b": "bval"}}
    recursive_update(d, {"a": {"b": "bval"}})
    assert d == {"a": {"b": "bval"}}


def test_openfile():
    """Test openfile()."""
    from paths import indir

    from tripper.utils import openfile

    with openfile(indir / "openfile.txt") as f:
        assert f.read().strip() == "Example file."

    with openfile(f"file:{indir}/openfile.txt") as f:
        assert f.read().strip() == "Example file."

    with openfile(f"file://{indir}/openfile.txt") as f:
        assert f.read().strip() == "Example file."

    with pytest.raises(IOError):
        with openfile("xxx://unknown_scheme"):
            pass


def test_openfile_http():
    """Test openfile()."""
    from tripper.utils import openfile

    pytest.importorskip("requests")

    with openfile(
        "https://raw.githubusercontent.com/EMMC-ASBL/tripper/refs/heads/"
        "master/tests/input/openfile.txt"
    ) as f:
        assert f.read().strip() == "Example file."


def infer_IRIs():
    """Test infer_IRIs"""
    from tripper import RDFS
    from tripper.utils import infer_iri

    # Test infer_iri()
    assert infer_iri(RDFS.subClassOf) == RDFS.subClassOf


def infer_Dlite_IRIs():
    """
    We have no dependencies on DLite, hence don't assume that it is installed.
    In case we have dlite, lets see if we can infer IRIs."""
    dlite = pytest.importorskip("dlite")
    from tripper.utils import infer_iri

    coll = dlite.Collection()
    assert infer_iri(coll.meta) == coll.meta.uri
    assert infer_iri(coll) == coll.uuid


def infer_SOFT7_IRIs():
    """
    We have no dependencies on pydantic, hence don't assume
    that it is installed.
    But if it is, infer_iri() should be able to infer
    IRIs from SOFT7 datamodels.
    """
    pytest.importorskip("pydantic")
    from typing import Any, Optional

    from pydantic import (  # pylint: disable=no-name-in-module,import-error
        AnyUrl,
        BaseModel,
        Field,
    )

    from tripper.utils import infer_iri

    class Property(BaseModel):
        """A property."""

        # pylint: disable=unsubscriptable-object
        # Yet another pylint bug, see
        # https://github.com/PyCQA/pylint/issues/1498
        type: Any = Field(..., description="Valid type name.")
        shape: Optional[list[str]] = Field(
            None, description="List of dimension expressions."
        )
        unit: Optional[str] = Field(None, description="Unit of a property.")
        description: Optional[str] = Field(
            None, description="A human description of the property."
        )

    class Entity(BaseModel):
        """An entity."""

        # pylint: disable=unsubscriptable-object
        identity: AnyUrl = Field(
            ..., description="Unique URI identifying the entity."
        )
        description: str = Field(
            "", description="A description of the entity."
        )
        dimensions: Optional[dict[str, str]] = Field(
            None, description="Dict mapping dimension names to descriptions."
        )
        properties: dict[str, Property] = Field(
            ..., description="Dict of properties."
        )

    user = Entity(
        identity="http://onto-ns.com/meta/0.1/User",
        properties={
            "username": Property(type=str, description="username"),
            "quota": Property(type=float, unit="GB", description="User quota"),
        },
    )

    assert infer_iri(user) == "http://onto-ns.com/meta/0.1/User"


def test_split_iri():
    """Test split_iri()"""
    from tripper import DCTERMS, RDFS
    from tripper.utils import split_iri

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


def test_function_id():
    """Test function_id()"""
    from tripper.utils import function_id

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


def test_bnode_iri():
    """Test bnode_iri()"""
    from tripper.utils import bnode_iri

    assert bnode_iri().startswith("_:")
    assert bnode_iri("abc").startswith("_:abc")
    assert len(bnode_iri("abc_", "src")) == 6 + 10
    assert len(bnode_iri("abc_", "src", 8)) == 6 + 16


# if True:
def test_tfilter():
    """Test filter()"""
    from tripper import FOAF, RDF, Namespace
    from tripper.utils import en, tfilter

    EX = Namespace("http://example.com#")
    triples = [
        (EX.Tom, RDF.type, EX.Cat),
        (EX.Tom, RDF.chaises, EX.Jerry),
        (EX.Tom, EX.pasPart, EX.Leg),
        (EX.Tom, FOAF.name, en("Tom")),
        (EX.Jerry, FOAF.name, en("Jerry")),
    ]
    assert set(tfilter(triples, predicate=FOAF.name)) == {
        (EX.Tom, FOAF.name, en("Tom")),
        (EX.Jerry, FOAF.name, en("Jerry")),
    }
    assert set(tfilter(triples, subject=EX.Tom, predicate=FOAF.name)) == {
        (EX.Tom, FOAF.name, en("Tom")),
    }
    assert set(
        tfilter(
            triples, subject=(EX.Tom, EX.Jerry, EX.Mammy), predicate=FOAF.name
        )
    ) == {
        (EX.Tom, FOAF.name, en("Tom")),
        (EX.Jerry, FOAF.name, en("Jerry")),
    }
    assert (
        set(tfilter(triples, subject=EX.Mammy, predicate=FOAF.name)) == set()
    )
    assert set(
        tfilter(triples, subject=[EX.Mammy, EX.Tom], predicate=FOAF.name)
    ) == {
        (EX.Tom, FOAF.name, en("Tom")),
    }
    assert set(tfilter(triples, predicate=[FOAF.email, EX.eats])) == set()
    assert set(tfilter(triples, object=[EX.Leg, EX.Arm])) == {
        (EX.Tom, EX.pasPart, EX.Leg),
    }

    # Test nested filters
    assert set(
        tfilter(triples=tfilter(triples, subject=EX.Tom), predicate=FOAF.name)
    ) == {(EX.Tom, FOAF.name, en("Tom"))}


def test_en():
    """Test en()"""
    from tripper import Literal
    from tripper.utils import en

    assert en("abc") == Literal("abc", lang="en")


def test_parse_literal():
    """Test parse_literal()"""

    from tripper import XSD, Literal
    from tripper.utils import parse_literal

    assert parse_literal("abc") == Literal("abc", datatype=XSD.string)
    assert parse_literal(True) == Literal("True", datatype=XSD.boolean)
    assert parse_literal(1) == Literal("1", datatype=XSD.integer)
    assert parse_literal(3.14) == Literal("3.14", datatype=XSD.double)
    assert parse_literal(f'"3.14"^^{XSD.double}') == Literal(
        "3.14", datatype=XSD.double
    )


def test_parse_object():
    """Test parse_object()"""
    from tripper import XSD, Literal
    from tripper.utils import parse_object

    assert parse_object("true") == Literal("true", datatype=XSD.boolean)
    assert parse_object("false") == Literal("false", datatype=XSD.boolean)
    assert parse_object("True") == Literal("True", datatype=XSD.string)
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
    assert parse_object("2022-12-01") == Literal(
        "2022-12-01", datatype=XSD.dateTime
    )
    assert parse_object("2022-12-01 12:30") == Literal(
        "2022-12-01 12:30", datatype=XSD.dateTime
    )
    assert parse_object("2022-12-01 12:30:30") == Literal(
        "2022-12-01 12:30:30", datatype=XSD.dateTime
    )
    assert parse_object("2022-12-01T12:30:30") == Literal(
        "2022-12-01T12:30:30", datatype=XSD.dateTime
    )
    assert parse_object("2022-12-01 12:30:30.500") == Literal(
        "2022-12-01 12:30:30.500", datatype=XSD.dateTime
    )
    # Format not supported in Python < 3.11
    # assert parse_object("2022-12-01 12:30:30Z") == Literal(
    #    "2022-12-01 12:30:30Z", datatype=XSD.dateTime
    # )
    assert parse_object("2022-12-01 12:30:30+01:00") == Literal(
        "2022-12-01 12:30:30+01:00", datatype=XSD.dateTime
    )
    assert parse_object("abc") == Literal("abc", datatype=XSD.string)
    assert parse_object('"abc"@en') == Literal("abc", lang="en")
    assert parse_object(str(XSD)) == str(XSD)
    assert parse_object(XSD.int) == XSD.int
    assert parse_object(f'"42"^^{XSD.integer}') == Literal(
        "42", datatype=XSD.integer
    )
    assert parse_object(f'"4.2"^^{XSD.double}') == Literal(
        "4.2", datatype=XSD.double
    )
    assert parse_object(f'"42"^^{XSD.double}') == Literal(
        "42.0", datatype=XSD.double
    )
    assert parse_object(f'"42"^^{XSD.int}') == Literal("42", datatype=XSD.int)


def test_as_python():
    """Test as_python()"""

    from tripper import XSD, Literal
    from tripper.utils import as_python

    assert as_python("abc") == "abc"
    assert as_python('"abc"@en') == "abc"
    assert as_python(f'"42"^^{XSD.double}') == 42
    assert as_python(Literal(32, datatype=XSD.integer)) == 32
    assert as_python(3.14) == 3.14


def test_random_string():
    """Test random_string()"""
    from tripper.utils import random_string

    rstring = random_string(16)
    assert isinstance(rstring, str)
    assert len(rstring) == 16
    assert rstring.isalnum()


# if True:
def test_extend_namespace():
    """Test extend namespace()"""
    pytest.importorskip("rdflib")
    from paths import ontodir

    from tripper import Namespace
    from tripper.errors import NoSuchIRIError
    from tripper.utils import extend_namespace

    FOOD = Namespace(
        "http://onto-ns.com/ontologies/examples/food#",
        label_annotations=True,
        check=True,
        reload=True,
        triplestore=ontodir / "food.ttl",
    )

    # Test extending with dict
    with pytest.raises(NoSuchIRIError):
        FOOD.Hamburger  # pylint: disable=pointless-statement

    extend_namespace(FOOD, {"Hamburger": FOOD + "Hamburger"})
    assert FOOD.Hamburger == FOOD + "Hamburger"

    # Test extending with triplestore
    with pytest.raises(NoSuchIRIError):
        FOOD.Fish  # pylint: disable=pointless-statement

    extend_namespace(FOOD, ontodir / "food-more.ttl")
    assert FOOD.Fish == FOOD + "FOOD_90f5dd54_9e5c_46c9_824f_e10625a90c26"

    EX = Namespace("http://example.com#")
    with pytest.raises(TypeError):
        extend_namespace(EX, {"Item": EX + "Item"})


def test_expand_iri():
    """Test expand_iri()."""
    pytest.importorskip("rdflib")

    from tripper import CHAMEO, DCTERMS, OTEIO, RDF
    from tripper.errors import NamespaceError
    from tripper.utils import expand_iri

    prefixes = {
        "chameo": str(CHAMEO),
        "dcterms": str(DCTERMS),
        "oteio": str(OTEIO),
        "rdf": str(RDF),
    }
    assert expand_iri("chameo:Sample", prefixes) == CHAMEO.Sample
    assert expand_iri("dcterms:title", prefixes) == DCTERMS.title
    assert expand_iri("oteio:Parser", prefixes) == OTEIO.Parser
    assert expand_iri("rdf:type", prefixes) == RDF.type
    assert expand_iri("xxx", prefixes) == "xxx"
    assert expand_iri("xxx:type", prefixes) == "xxx:type"
    with pytest.raises(NamespaceError):
        expand_iri("xxx:type", prefixes, strict=True)


def test_prefix_iri():
    """Test prefix_iri()."""
    pytest.importorskip("rdflib")

    from tripper import CHAMEO, DCTERMS, OTEIO, RDF
    from tripper.errors import NamespaceError
    from tripper.utils import prefix_iri

    prefixes = {
        "chameo": str(CHAMEO),
        "dcterms": str(DCTERMS),
        "oteio": str(OTEIO),
        "rdf": str(RDF),
    }
    assert prefix_iri(CHAMEO.Sample, prefixes) == "chameo:Sample"
    assert prefix_iri(DCTERMS.title, prefixes) == "dcterms:title"
    assert prefix_iri(OTEIO.Parser, prefixes) == "oteio:Parser"
    assert prefix_iri(RDF.type, prefixes) == "rdf:type"
    assert prefix_iri("xxx", prefixes) == "xxx"
    with pytest.raises(NamespaceError):
        prefix_iri("xxx", prefixes, require_prefixed=True)


def test_get_entry_points():
    """Test get_entry_points()"""
    from tripper.utils import get_entry_points

    for ep in get_entry_points("tripper.keywords"):
        if ep.value == "default":
            break
    else:
        raise RuntimeError(
            "no tripper.keywords entry point with value 'default'"
        )
