"""Test RDF serialisation."""

# pylint: disable=invalid-name,too-many-locals

from pathlib import Path

import pytest

pytest.importorskip("yaml")
pytest.importorskip("requests")

thisdir = Path(__file__).resolve().parent
testdir = thisdir.parent
inputdir = testdir / "input"
outputdir = testdir / "output"


def test_get_context():
    """Test get_context()."""
    from tripper.dataset import get_context

    context = get_context()
    assert isinstance(context, dict)
    assert "@version" in context
    assert len(context) > 20


def test_get_prefixes():
    """Test get_prefixes()."""
    from tripper.dataset import get_prefixes

    prefixes = get_prefixes()
    assert prefixes["dcat"] == "http://www.w3.org/ns/dcat#"
    assert prefixes["emmo"] == "https://w3id.org/emmo#"


def test_get_shortnames():
    """Test get_shortnames()."""
    from tripper import DCTERMS
    from tripper.dataset.dataset import get_shortnames

    # Short names that are not equal to the last component of the IRI
    exceptions = (
        "datamodel",
        "datamodelStorage",
        "prefixes",
        "configuration",
        "statements",
        "@type",
    )

    shortnames = get_shortnames()
    assert shortnames[DCTERMS.title] == "title"

    for k, v in shortnames.items():
        if v not in exceptions:
            assert k.rsplit("#", 1)[-1].rsplit("/", 1)[-1] == v


# def test_expand_prefixes():
#     """Test expand_prefixes()."""
#     from tripper import DCTERMS, EMMO, OTEIO
#     from tripper.dataset.dataset import expand_prefixes, get_prefixes
#
#     prefixes = get_prefixes()
#     d = {
#         "a": "oteio:Parser",
#         "b": [
#             "emmo:Atom",
#             {
#                 "Z": "emmo:AtomicNumber",
#                 "v": "dcterms:a/b",
#             },
#         ],
#     }
#     expand_prefixes(d, prefixes)
#     assert d["a"] == OTEIO.Parser
#     assert d["b"][0] == EMMO.Atom
#     assert d["b"][1]["Z"] == EMMO.AtomicNumber
#     assert d["b"][1]["v"] == DCTERMS["a/b"]


def test_add():
    """Test help-function add()."""
    from tripper.dataset.dataset import add

    d = {}
    add(d, "a", 1)
    add(d, "b", 1)
    add(d, "b", 1)
    add(d, "a", 2)
    add(d, "a", 1)
    assert d == {"a": [1, 2], "b": 1}


def test_get():
    """Test help-function get()."""
    from tripper.dataset.dataset import get

    d = {"a": [1, 2], "b": 1}
    assert get(d, "a") == [1, 2]
    assert get(d, "b") == [1]
    assert get(d, "b", aslist=False) == 1
    assert get(d, "c") == []
    assert get(d, "c", default="x") == ["x"]
    assert get(d, "c", aslist=False) is None
    assert get(d, "c", default="x", aslist=False) == "x"


def test_expand_iri():
    """Test help-function expand_iri()."""
    from tripper import CHAMEO, DCTERMS, OTEIO, RDF
    from tripper.dataset.dataset import expand_iri, get_prefixes

    prefixes = get_prefixes()
    assert expand_iri("chameo:Sample", prefixes) == CHAMEO.Sample
    assert expand_iri("dcterms:title", prefixes) == DCTERMS.title
    assert expand_iri("oteio:Parser", prefixes) == OTEIO.Parser
    assert expand_iri("rdf:type", prefixes) == RDF.type
    assert expand_iri("xxx", prefixes) == "xxx"
    with pytest.warns(UserWarning):
        assert expand_iri("xxx:type", prefixes) == "xxx:type"


# if True:
def test_save_and_load():
    """Test save_datadoc() and load()."""

    from tripper import CHAMEO, DCAT, OTEIO, Triplestore
    from tripper.dataset import (
        list_dataset_iris,
        load,
        load_dict,
        save,
        save_datadoc,
        save_dict,
    )

    pytest.importorskip("dlite")

    ts = Triplestore("rdflib")

    # Load data documentation into triplestore
    datadoc = save_datadoc(ts, inputdir / "semdata.yaml")
    assert isinstance(datadoc, dict)
    assert "@context" in datadoc

    # Test load dict-representation of a dataset from the triplestore
    SEM = ts.namespaces["sem"]
    SEMDATA = ts.namespaces["semdata"]
    iri = SEMDATA["SEM_cement_batch2/77600-23-001/77600-23-001_5kV_400x_m001"]
    d = load_dict(ts, iri, use_sparql=False)
    assert d["@id"] == iri
    assert set(d["@type"]) == {DCAT.Dataset, SEM.SEMImage}
    assert d.inSeries == SEMDATA["SEM_cement_batch2/77600-23-001"]
    assert d.distribution.mediaType == "image/tiff"

    # Test load using SPARQL - this should give the same result as above
    d2 = load_dict(ts, iri, use_sparql=True)
    assert d2 == d

    # Test loading a parser
    PARSER = ts.namespaces["parser"]
    parser = load_dict(ts, PARSER.sem_hitachi)
    assert parser["@id"] == PARSER.sem_hitachi
    assert parser["@type"] == OTEIO.Parser
    assert parser.configuration == {"driver": "hitachi"}
    assert parser.parserType == "application/vnd.dlite-parse"
    assert parser == d.distribution.parser

    # Test saving a generator and add it to the distribution
    GEN = ts.bind("gen", "http://sintef.no/dlite/generator#")
    generator = {
        "@id": GEN.sem_hitachi,
        "generatorType": "application/vnd.dlite-generate",
        "configuration": {"driver": "hitachi"},
    }
    save_dict(ts, "generator", generator)
    ts.add((d.distribution["@id"], OTEIO.generator, generator["@id"]))
    dist = load_dict(ts, d.distribution["@id"])
    assert dist.generator["@id"] == GEN.sem_hitachi
    assert dist.generator["@type"] == OTEIO.Generator
    assert dist.generator.generatorType == "application/vnd.dlite-generate"

    # Test load dataset (this downloads an actual image from github)
    data = load(ts, iri)
    assert len(data) == 53502

    # Test load updated distribution
    dd = load_dict(ts, iri)
    assert dd != d  # we have added a generator
    assert dd.distribution.generator == load_dict(ts, generator["@id"])

    # Test save dataset
    newfile = outputdir / "newimage.tiff"
    newfile.unlink(missing_ok=True)
    distribution = {
        "@id": SEMDATA.newimage,
        "@type": SEM.SimImage,
        "downloadURL": f"file:{newfile}",
    }
    buf = b"some bytes..."
    save(ts, buf, distribution=distribution)
    assert newfile.exists()
    assert newfile.stat().st_size == len(buf)

    # Test load new distribution
    # dnew = load_dict(ts, SEMDATA.newimage)

    # Test searching the triplestore
    SAMPLE = ts.namespaces["sample"]
    assert set(list_dataset_iris(ts)) == {
        SEMDATA["SEM_cement_batch2/77600-23-001/77600-23-001_5kV_400x_m001"],
        SEMDATA["SEM_cement_batch2/77600-23-001"],
        SEMDATA["SEM_cement_batch2"],
        SAMPLE["SEM_cement_batch2/77600-23-001"],
    }
    assert set(list_dataset_iris(ts, creator="Sigurd Wenner")) == {
        SEMDATA["SEM_cement_batch2/77600-23-001/77600-23-001_5kV_400x_m001"],
        SEMDATA["SEM_cement_batch2/77600-23-001"],
        SEMDATA["SEM_cement_batch2"],
    }
    assert set(list_dataset_iris(ts, _type=CHAMEO.Sample)) == {
        SAMPLE["SEM_cement_batch2/77600-23-001"],
    }


def test_fuseki():
    """Test save and load dataset with Fuseki."""
    import os

    from tripper import Triplestore

    host = os.getenv("TRIPLESTORE_HOST", "localhost")
    port = os.getenv("TRIPLESTORE_PORT", "3030")
    fuseki_args = {
        "backend": "fusekix",
        "base_iri": "http://example.com/ontology#",
        "triplestore_url": f"http://{host}:{port}",
        "database": "openmodel",
    }
    try:
        ts = Triplestore(**fuseki_args)
    except ModuleNotFoundError:
        pytest.skip("Cannot connect to Fuseki server")
    ts.remove_database(**fuseki_args)
