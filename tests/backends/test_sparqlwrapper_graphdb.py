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


def test_graphdb():
    """
    Test the sparqlwrapper backend using GraphDB.
    """
    # Check if GraphDB is available and write a warning if it is not.
    if not graphdb_available():
        pytest.skip("GraphDB instance not available locally; skipping tests.")

    from pathlib import Path

    from tripper import Literal, Triplestore
    from tripper.datadoc import load_dict, save_datadoc, search_iris

    thisdir = Path(__file__).resolve().parent
    datasetinput = thisdir / "datadocumentation_sample.yaml"

    ts = Triplestore(
        backend="sparqlwrapper",
        base_iri="http://localhost:7200/repositories/test_repo",
        update_iri="http://localhost:7200/repositories/test_repo/statements",
    )

    # Test adding triples
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
                Literal("b"),
            ),
        ]
    )

    # Test SELECT query
    query_object = (
        "SELECT ?s ?p ?o WHERE { <http://www.example.org/subject> ?p ?o }"
    )

    # Run the query using your triplestore instance.
    result = ts.query(query_object)

    assert set(
        [
            ("http://www.example.org/predicate", "a"),
            ("http://www.example.org/predicate", "b"),
        ]
    ) == set(result)

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
    result_generator = ts.query(query)
    assert (
        "http://www.example.org/subject",
        "http://www.example.org/predicate",
        "a",
    ) in result_generator

    # Test ASK query
    query = """
ASK {
<http://www.example.org/subject> <http://www.example.org/predicate> 'a' }
"""
    # Check that it raises NotImplementedError
    with pytest.raises(NotImplementedError):
        ts.query(query)

    # Test DESCRIBE query
    query = "DESCRIBE <http://www.example.org/subject>"
    # Check that it raises NotImplementedError
    with pytest.raises(NotImplementedError):
        ts.query(query)

    # save a dataset to the graphDB
    save_datadoc(ts, datasetinput)

    # search for datasets in the graphDB
    datasets = search_iris(ts, type="dataset")

    assert datasets == ["https://onto-ns.com/datasets/our_nice_dataset"]

    retreived_info = load_dict(ts, datasets[0])
    assert retreived_info.creator == "Tripper-team"
    assert (
        retreived_info.title
        == "This is a title of a completely invented dataset"
    )
