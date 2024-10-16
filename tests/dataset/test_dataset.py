"""Test RDF serialisation."""

from pathlib import Path

import pytest

pytest.importorskip("yaml")
pytest.importorskip("requests")

thisdir = Path(__file__).resolve().parent
testdir = thisdir.parent
inputdir = testdir / "input"


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
    from tripper.dataset import get_shortnames

    # Short names that are not equal to the last component of the IRI
    exceptions = (
        "datamodel",
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


def test_expand_prefixes():
    """Test expand_prefixes()."""
    from tripper import DCTERMS, EMMO, OTEIO
    from tripper.dataset import expand_prefixes, get_prefixes

    prefixes = get_prefixes()
    d = {
        "a": "oteio:Parser",
        "b": [
            "emmo:Atom",
            {
                "Z": "emmo:AtomicNumber",
                "v": "dcterms:a/b",
            },
        ],
    }
    expand_prefixes(d, prefixes)
    assert d["a"] == OTEIO.Parser
    assert d["b"][0] == EMMO.Atom
    assert d["b"][1]["Z"] == EMMO.AtomicNumber
    assert d["b"][1]["v"] == DCTERMS["a/b"]


# if True:
def test_save_and_load_dataset():
    """Test save_dataset() and load_dataset()."""
    ## pylint: disable=too-many-locals,invalid-name

    from tripper import DCAT, OTEIO, Triplestore
    from tripper.dataset import load_dataset, load_parser, save_datadoc

    ts = Triplestore("rdflib")

    # Load data documentation into triplestore
    datadoc = save_datadoc(ts, inputdir / "semdata.yaml")
    assert isinstance(datadoc, dict)
    assert "@context" in datadoc

    # Load back dict representation from the triplestore
    SEM = ts.namespaces["sem"]
    SEMDATA = ts.namespaces["semdata"]
    iri = SEMDATA["SEM_cement_batch2/77600-23-001/77600-23-001_5kV_400x_m001"]
    d = load_dataset(ts, iri)
    assert d["@id"] == iri
    assert set(d["@type"]) == {DCAT.Dataset, SEM.SEMImage}
    assert d.inSeries == SEMDATA["SEM_cement_batch2/77600-23-001"]
    assert d.distribution["downloadURL"] == (
        "sftp://nas.aimen.es/P_MATCHMAKER_SHARE_SINTEF/"
        "SEM_cement_batch2/77600-23-001/77600-23-001_5kV_400x_m001.tif"
    )
    assert d.distribution["mediaType"] == "image/tiff"

    PARSER = ts.namespaces["parser"]
    parser = load_parser(ts, PARSER.sem_hitachi)
    assert parser["@id"] == PARSER.sem_hitachi
    assert parser["@type"] == OTEIO.Parser
    assert parser.configuration == {"driver": "hitachi"}
    assert parser.parserType == "application/vnd.dlite-parse"


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
