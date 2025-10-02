"""
Test the sparqlwrapper backend with GraphDB.
Note that this requires to have a running graphDB instance set up
as described in the for_developers documentation on
https://emmc-asbl.github.io/tripper/latest/developers/.
"""

from pathlib import Path

import pytest

from tripper import Session

pytest.importorskip("pyld")

thisdir = Path(__file__).resolve().parent
indir = thisdir.parent / "input"

session = Session(config=indir / "session.yaml")


# if True:
#    sessionName = "GraphDBTest"
#    sessionName = "FusekiTest"
def populate_and_search(sessionName):  # pylint: disable=too-many-statements
    """Do the test on the desried backend."""
    # pylint: disable=too-many-locals

    from tripper import Literal
    from tripper.datadoc import acquire, save_datadoc, search

    ts = session.get_triplestore(sessionName)
    if not ts.available(timeout=1):
        pytest.skip(f"{sessionName} service not available; skipping test.")

    datasetinput = thisdir / "datadocumentation_sample.yaml"
    datasetinput2 = thisdir / "datadocumentation_sample2.yaml"

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
    datasets = search(ts, type="Dataset")

    print("Found datasets:")
    print(datasets)
    assert set(datasets) == set(
        [
            "https://onto-ns.com/datasets#our_nice_dataset",
            "https://onto-ns.com/datasets#our_nice_dataset2",
        ]
    )

    retreived_info = acquire(ts, datasets[0])
    # print("Info on one dataset")
    # print(retreived_info)
    assert retreived_info.creator.name == "Tripper-team"
    assert (
        retreived_info.title
        == "This is a title of a completely invented dataset"
    )

    ts.bind("dataset", "https://onto-ns.com/datasets#")
    retreived_info_2 = acquire(ts, f"dataset:{datasets[0].split('#')[-1]}")
    # print(retreived_info_2)
    assert retreived_info_2.creator.name == "Tripper-team"
    assert (
        retreived_info_2.title
        == "This is a title of a completely invented dataset"
    )

    # assert retreived_info == retreived_info_2 # When PR342 is accepted

    ts.remove(subject="https://onto-ns.com/datasets#our_nice_dataset2")

    datasets3 = search(ts, type="Dataset")

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
    """Test the sparqlwrapper backend using GraphDB."""
    # Use service configured in tests/input/session.yaml
    populate_and_search("GraphDBTest")


def test_fuseki():
    """Test the sparqlwrapper backend using Fuseki."""
    # Use service configured in tests/input/session.yaml
    populate_and_search("FusekiTest")
