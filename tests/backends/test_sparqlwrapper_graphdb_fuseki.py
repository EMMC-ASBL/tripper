"""
Test the sparqlwrapper backend with GraphDB.
Note that this requires to have a running graphDB instance set up
as described in the for_developers documentation on
https://emmc-asbl.github.io/tripper/latest/developers/.
"""

import time

import pytest
import requests

# URL to check if GraphDB is running.
GRAPHDB_CHECK_URL = "http://localhost:7200/repositories"
FUSEKI_CHECK_URL = "http://localhost:3030"


def graphdb_available():
    """
    Help function that checks if the GraphDB instance is available.
    If it is not, the tests that depend on it will be skipped.
    """
    timeout = 10  # seconds
    interval = 1  # seconds
    start_time = time.time()
    while True:
        try:
            response = requests.get(GRAPHDB_CHECK_URL, timeout=timeout)
            if response.status_code == 200:
                return True
        except requests.exceptions.RequestException:
            pass

        if time.time() - start_time > timeout:
            return False
        time.sleep(interval)


def fuseki_available():
    """
    Help function that checks if the Fuseki instance is available
    """
    timeout = 10  # seconds
    interval = 1  # seconds
    start_time = time.time()
    while True:
        try:
            response = requests.get(FUSEKI_CHECK_URL, timeout=timeout)
            if response.status_code == 200:
                return True
        except requests.exceptions.RequestException:
            pass

        if time.time() - start_time > timeout:
            return False
        time.sleep(interval)


def get_triplestore(tsname: str) -> "Triplestore":
    """Help function that returns a new triplestore object."""
    from tripper import Triplestore

    if tsname == "GraphDB":
        ts = Triplestore(
            backend="sparqlwrapper",
            base_iri="http://localhost:7200/repositories/test_repo",
            update_iri=(
                "http://localhost:7200/repositories/test_repo/statements"
            ),
        )
    elif tsname == "Fuseki":
        ts = Triplestore(
            backend="sparqlwrapper",
            base_iri=f"{FUSEKI_CHECK_URL}/test_repo",
            update_iri=f"{FUSEKI_CHECK_URL}/test_repo/update",
            username="admin",
            password="admin0",
        )
    else:
        raise ValueError(f"Unsupported triplestore name: {tsname}")

    return ts


def populate_and_search(tsname):
    """Do the test on the desried backend."""
    # Test adding triples

    from pathlib import Path

    from tripper import Literal
    from tripper.datadoc import load_dict, save_datadoc, search_iris

    thisdir = Path(__file__).resolve().parent
    datasetinput = thisdir / "datadocumentation_sample.yaml"
    datasetinput2 = thisdir / "datadocumentation_sample2.yaml"

    ts = get_triplestore(tsname)

    ts.add_triples(
        [
            (
                "http://www.example.org/subject",
                "http://www.example.org/predicate",
                Literal("a"),
            ),
            (
                "http://www.example.org/subject",
                "http://www.example.org/predicate",
                Literal(1.0),
            ),
        ]
    )

    # Test SELECT query
    query_object = (
        "SELECT ?p ?o WHERE { <http://www.example.org/subject> ?p ?o }"
    )

    # Run the query using your triplestore instance.
    result = ts.query(query_object)

    assert set(result) == {
        ("http://www.example.org/predicate", Literal("a")),
        ("http://www.example.org/predicate", Literal(1.0)),
    }

    # Test CONSTRUCT query
    # NB adding the PREFIX just to show that it works.
    query = """
PREFIX : <http://example.com#>
CONSTRUCT { ?s ?p ?o }
WHERE {
  <http://www.example.org/subject> ( : | !( : ) )* ?o .
  ?s ?p ?o .
}
"""

    # Run the query.
    results = set(ts.query(query))
    assert (
        "http://www.example.org/subject",
        "http://www.example.org/predicate",
        Literal("a"),
    ) in results
    assert (
        "http://www.example.org/subject",
        "http://www.example.org/predicate",
        Literal(1.0),
    ) in results

    # Test ASK query
    query = """
ASK {
<http://www.example.org/subject> <http://www.example.org/predicate> 'a' }
"""
    # Check that it raises NotImplementedError
    with pytest.raises(NotImplementedError):
        ts.query(query)

    # Test DELETE query - clear the triplestore
    ts.update("DELETE WHERE { ?s ?p ?o . }")

    # Test DESCRIBE query
    query = "DESCRIBE <http://www.example.org/subject>"
    # Check that it raises NotImplementedError
    with pytest.raises(NotImplementedError):
        ts.query(query)

    # save a dataset to triplestore
    save_datadoc(ts, datasetinput)
    save_datadoc(ts, datasetinput2)

    # search for datasets in triplestore
    datasets = search_iris(ts, type="dataset")

    print("Found datasets:")
    print(datasets)
    assert set(datasets) == set(
        [
            "https://onto-ns.com/datasets#our_nice_dataset",
            "https://onto-ns.com/datasets#our_nice_dataset2",
        ]
    )

    retreived_info = load_dict(ts, datasets[0])
    print("Info on one dataset")
    print(retreived_info)
    assert retreived_info.creator == "Tripper-team"
    assert (
        retreived_info.title
        == "This is a title of a completely invented dataset"
    )

    ts.bind("dataset", "https://onto-ns.com/datasets#")
    retreived_info_2 = load_dict(ts, f"dataset:{datasets[0].split('#')[-1]}")
    print(retreived_info_2)
    assert retreived_info_2.creator == "Tripper-team"
    assert (
        retreived_info_2.title
        == "This is a title of a completely invented dataset"
    )

    # assert retreived_info == retreived_info_2 # When PR342 is accepted

    ts.remove(subject="https://onto-ns.com/datasets#our_nice_dataset2")

    datasets3 = search_iris(ts, type="dataset")

    print("Found datasets after deletion:")
    print(datasets3)
    assert set(datasets3) == set(
        [
            "https://onto-ns.com/datasets#our_nice_dataset",
        ]
    )

    # Test INSERT query
    query = """
PREFIX : <http://example.com#>
INSERT DATA {
    :sub :pred :obj .
}
"""
    EX = ts.bind("ex", "http://example.com#")
    ts.update(query)
    triples = list(ts.triples(EX.sub))
    assert triples == [(EX.sub, EX.pred, EX.obj)]


def test_graphdb():
    """
    Test the sparqlwrapper backend using GraphDB.
    """
    # Check if GraphDB is available and write a warning if it is not.
    if not graphdb_available():
        pytest.skip("GraphDB instance not available locally; skipping tests.")

    print("Testing graphdb")
    populate_and_search("GraphDB")


def test_fuseki():
    """
    Test the sparqlwrapper backend using Fuseki.
    """
    # Check if Fuseki is available and write a warning if it is not.
    if not fuseki_available():
        pytest.skip("Fuseki instance not available locally; skipping tests.")

    print("Testing fuseki")
    populate_and_search("Fuseki")
