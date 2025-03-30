"""
Test the sparqlwrapper backend with GraphDB.
Note that this requires to have a running graphDB instance set up
as described in the for_developers documentation on
https://emmc-asbl.github.io/tripper/latest/developers/.
"""

import pytest

# URL to check if GraphDB is running.
GRAPHDB_CHECK_URL = "http://localhost:7200/repositories"
FUSEKI_CHECK_URL = "http://localhost:3030"


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


# if True:
#    tsname = "Fuseki"
def populate_and_search(tsname):  # pylint: disable=too-many-statements
    """Do the test on the desried backend."""
    # pylint: disable=too-many-locals

    from pathlib import Path

    from tripper import Literal
    from tripper.datadoc import load_dict, save_datadoc, search_iris

    thisdir = Path(__file__).resolve().parent
    datasetinput = thisdir / "datadocumentation_sample.yaml"
    datasetinput2 = thisdir / "datadocumentation_sample2.yaml"

    ts = get_triplestore(tsname)
    EX = ts.bind("ex", "http://www.example.org/")

    # Test DELETE query - clear the triplestore
    ts.update("DELETE WHERE { ?s ?p ?o . }")

    # Add some triples
    ts.add_triples(
        [
            (EX.subject, EX.predicate, Literal("a")),
            (EX.subject, EX.predicate, Literal(1.0)),
            (EX.subject2, EX.predicate, EX.obj),
        ]
    )

    # Test SELECT query
    query = "SELECT ?p ?o WHERE { <http://www.example.org/subject> ?p ?o }"
    result = ts.query(query)
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
    query1 = """
ASK {
  <http://www.example.org/subject> <http://www.example.org/predicate> "a" .
}
"""
    query2 = """
ASK {
  <http://www.example.org/subject> <http://www.example.org/predicate> "b" .
}
"""
    query3 = """
PREFIX ex: <http://www.example.org/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
ASK {
  ex:subject ex:predicate "1.0"^^xsd:double .
}
"""
    assert ts.query(query1) is True
    assert ts.query(query2) is False
    assert ts.query(query3) is True

    # Test DESCRIBE query
    query = "DESCRIBE <http://www.example.org/subject>"
    triples = set(ts.query(query))
    assert triples == set(
        [
            (EX.subject, EX.predicate, Literal("a")),
            (EX.subject, EX.predicate, Literal(1.0)),
        ]
    )

    # save a dataset to triplestore
    save_datadoc(ts, datasetinput)
    save_datadoc(ts, datasetinput2)

    # search for datasets in triplestore
    datasets = search_iris(ts, type="Dataset")

    print("Found datasets:")
    print(datasets)
    assert set(datasets) == set(
        [
            "https://onto-ns.com/datasets#our_nice_dataset",
            "https://onto-ns.com/datasets#our_nice_dataset2",
        ]
    )

    retreived_info = load_dict(ts, datasets[0])
    # print("Info on one dataset")
    # print(retreived_info)
    assert retreived_info.creator.name == "Tripper-team"
    assert (
        retreived_info.title
        == "This is a title of a completely invented dataset"
    )

    ts.bind("dataset", "https://onto-ns.com/datasets#")
    retreived_info_2 = load_dict(ts, f"dataset:{datasets[0].split('#')[-1]}")
    # print(retreived_info_2)
    assert retreived_info_2.creator.name == "Tripper-team"
    assert (
        retreived_info_2.title
        == "This is a title of a completely invented dataset"
    )

    # assert retreived_info == retreived_info_2 # When PR342 is accepted

    ts.remove(subject="https://onto-ns.com/datasets#our_nice_dataset2")

    datasets3 = search_iris(ts, type="Dataset")

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
    from tripper.utils import check_service_availability

    if not check_service_availability(GRAPHDB_CHECK_URL, timeout=1):
        pytest.skip("GraphDB instance not available locally; skipping tests.")

    print("Testing graphdb")
    populate_and_search("GraphDB")


def test_fuseki():
    """
    Test the sparqlwrapper backend using Fuseki.
    """
    # Check if Fuseki is available and write a warning if it is not.
    from tripper.utils import check_service_availability

    if not check_service_availability(FUSEKI_CHECK_URL, timeout=1):
        pytest.skip("Fuseki instance not available locally; skipping tests.")

    print("Testing fuseki")
    populate_and_search("Fuseki")
