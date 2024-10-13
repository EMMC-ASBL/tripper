"""Test RDF serialisation."""

from pathlib import Path

thisdir = Path(__file__).resolve().parent
testdir = thisdir.parent
inputdir = testdir / "input"


# if True:
def test_save_and_load_dataset():
    """Test save_dataset() and load_dataset()."""
    # pylint: disable=too-many-locals,invalid-name

    import os

    # from paths import inputdir, outputdir
    from tripper import Triplestore
    from tripper.dataset import load_datadoc

    backend = "rdflib"
    TRIPLESTORE_HOST = os.getenv("TRIPLESTORE_HOST", "localhost")
    TRIPLESTORE_PORT = os.getenv("TRIPLESTORE_PORT", "3030")
    fuseki_args = {
        "backend": "fuseki",
        "base_iri": "http://example.com/ontology#",
        "triplestore_url": f"http://{TRIPLESTORE_HOST}:{TRIPLESTORE_PORT}",
        "database": "openmodel",
    }

    # Connect to triplestore
    if backend == "fuseki":
        ts = Triplestore(**fuseki_args)
        ts.remove_database(**fuseki_args)
    else:
        ts = Triplestore("rdflib")

    # Load data documentation
    datadoc = load_datadoc(inputdir / "datasets.yaml")
    assert isinstance(datadoc, dict)
    assert "@context" in datadoc

    # # Store dict representation of the dataset to triplestore
    # ds = save_dataset(ts, dataset, prefixes=prefixes)
    # repr1 = set(ts.triples())
    #
    # # Load back dict representation from the triplestore
    # EX = ts.namespaces["ex"]
    # d = load_dataset(ts, iri=EX.mydata)
    #
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
