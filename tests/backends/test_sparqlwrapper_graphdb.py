"""
Test the sparqlwrapper backend with GraphDB.
Note that this requires to have a running graphDB instance set up
as described in the for_developers documentation.
"""

import time

import pytest
import requests

# URL to check if GraphDB is running.
GRAPHDB_CHECK_URL = "http://localhost:7200/repositories"


def graphdb_available():
    """
    Fixture that checks if the GraphDB instance is available.
    If it is not, the tests that depend on it will be skipped.
    """
    timeout = 10  # seconds
    interval = 1  # seconds
    start_time = time.time()
    while True:
        try:
            response = requests.get(GRAPHDB_CHECK_URL, timeout=timeout)
            if response.status_code == 200:
                break  # GraphDB is up!
        except requests.exceptions.RequestException:
            pass

        if time.time() - start_time > timeout:
            pytest.skip(
                "GraphDB instance not available locally; skipping tests."
            )
        time.sleep(interval)
    # If we get here, GraphDB is up.
    yield


def test_graphdb():
    """
    Fixture that creates a Triplestore instance.
    This will only be used if the GraphDB instance is available.
    """
    # Check if GraphDB is available and write a warning if it is not.
    if not graphdb_available():
        pytest.skip("GraphDB instance not available locally; skipping tests.")

    from tripper import Literal, Triplestore

    # from tripper.datadoc import load_dict, save_datadoc, search_iris

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
