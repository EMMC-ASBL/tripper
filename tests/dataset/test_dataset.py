"""Test RDF serialisation."""

from pathlib import Path

import pytest

pytest.importorskip("yaml")
pytest.importorskip("requests")

thisdir = Path(__file__).resolve().parent
testdir = thisdir.parent
inputdir = testdir / "input"


if True:
    # def test_save_and_load_dataset():
    """Test save_dataset() and load_dataset()."""
    # pylint: disable=too-many-locals,invalid-name

    from tripper import DCAT, RDF, Triplestore
    from tripper.dataset import load_datadoc, load_dataset, save_dataset

    ts = Triplestore("rdflib")

    # Load data documentation
    # datadoc = load_datadoc(inputdir / "datasets.yaml")
    datadoc = load_datadoc(inputdir / "semdata.yaml")
    assert isinstance(datadoc, dict)
    assert "@context" in datadoc

    prefixes = datadoc["prefixes"]
    for dataset in datadoc["datasets"]:
        ds = save_dataset(ts, dataset, prefixes=prefixes)
        repr1 = set(ts.triples())

    # Load back dict representation from the triplestore
    SEMDATA = ts.namespaces["semdata"]
    d = load_dataset(ts, iri=SEMDATA["sample3/pos1_01_grid_200x"])

    # Should the prefix be expanded?
    assert ds["@id"] == "semdata:sample3/pos1_01_grid_200x"

    assert (
        "semdata:sample3/pos1_01_grid_200x",
        RDF.type,
        DCAT.Dataset,
    ) in repr1
    assert d["@id"] == (
        "http://sintef.no/data/matchmaker/SEM/sample3/pos1_01_grid_200x"
    )
    # # Store the new dict representation to another triplestore
    # ts2 = Triplestore("rdflib")
    # ds2 = save_dataset(ts2, d)
    # repr2 = set(ts.triples())
    #
    # # Ensure that both dict and triplestore representations are equal
    # assert ds2 == ds
    # assert repr2 == repr1
    #
    # # Load dataset using SPARQL
    # dd = load_dataset_sparql(ts, iri=EX.mydata)
    # assert dd == d


# if True:
def test_datadoc():
    """Test storing data documentation to triplestore."""
    # pylint: disable=unused-variable
    import io
    import json

    from tripper import Triplestore
    from tripper.dataset import load_datadoc

    ts = Triplestore("rdflib")
    d = load_datadoc(inputdir / "datasets.yaml")

    f = io.StringIO(json.dumps(d))
    ts2 = Triplestore(backend="rdflib")
    ts2.parse(f, format="json-ld")

    # Add triples from temporary triplestore
    ts.add_triples(ts2.triples())
    # ts2.close()  # explicit close ts2

    print(ts.serialize())


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
