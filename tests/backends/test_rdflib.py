"""Test rdflib backend.

Most of the rdflib backend is already tested in tests/test_triplestore.py.
"""

import pytest

pytest.importorskip("rdflib")

# pylint: disable=invalid-name


def test_rdflib_backend():
    """Test rdflib backend."""

    from tripper import RDFS, Literal, Triplestore

    ts = Triplestore("rdflib")
    EX = ts.bind("", "http://ex#")

    # Test for issue #162: Literals are lost when accessing triples with rdflib
    ts.parse(
        format="turtle",
        data=(
            "<http://ex#s> <http://ex#p> "
            '"abc"^^<http://www.w3.org/2001/XMLSchema#string> .'
        ),
    )
    assert list(ts.triples()) == [
        (
            "http://ex#s",
            "http://ex#p",
            Literal("abc", datatype="http://www.w3.org/2001/XMLSchema#string"),
        )
    ]

    # Test for bnode
    ts.add_triples([("_:bn1", RDFS.subClassOf, EX.s)])
    assert ts.value(predicate=RDFS.subClassOf, object=EX.s) == "_:bn1"

    assert ts.prefer_sparql is False


def test_rdflib_triplestore_url():
    """Test loading an rdflib triplestore using the `triplestore_url`
    argument."""
    from pathlib import Path

    from tripper import FOAF, RDF, Namespace, Triplestore

    testdir = Path(__file__).resolve().parent.parent
    inputdir = testdir / "input"

    ts = Triplestore("rdflib", triplestore_url=inputdir / "testkb.ttl")
    assert "ex" in ts.namespaces
    EX = Namespace(ts.namespaces["ex"])
    assert ts.has(EX.JohnDow, RDF.type, FOAF.Person)


def test_backend_rdflib(expected_function_triplestore: str) -> None:
    """Specifically test the rdflib backend Triplestore.

    Parameters:
        expected_function_triplestore: Fixture from `conftest.py`, which
            returns a Turtle-serialized string of what is expected when
            serializing the Triplestore in this test.

    """
    pytest.importorskip("rdflib")
    from tripper.triplestore import RDFS, Triplestore

    ts = Triplestore("rdflib")
    EX = ts.bind(
        "ex", "http://example.com/onto#"
    )  # pylint: disable=invalid-name
    ts.parse(format="turtle", data=expected_function_triplestore)
    assert ts.serialize(format="turtle") == expected_function_triplestore
    ts.set((EX.AnotherConcept, RDFS.subClassOf, EX.MyConcept))

    def cost(parameter):
        return 2 * parameter

    ts.add_mapsTo(
        EX.Sum, "http://onto-ns.com/meta/0.1/MyEntity#sum", cost=cost
    )
    assert (  # pylint: disable=comparison-with-callable
        list(ts.function_repo.values())[0] == cost
    )

    def func(parameter):
        return parameter + 1

    ts.add_function(func, expects=EX.Sum, returns=EX.OneMore, cost=cost)
    assert (  # pylint: disable=comparison-with-callable
        list(ts.function_repo.values())[1] == func
    )
    assert len(ts.function_repo) == 2  # cost is only added once

    def func2(parameter):
        return parameter + 2

    def cost2(parameter):
        return 2 * parameter + 1

    ts.add_function(func2, expects=EX.Sum, returns=EX.EvenMore, cost=cost2)
    assert len(ts.function_repo) == 4


def test_backend_rdflib_base_iri(
    get_ontology_path: "Callable[[str], Path]", tmp_path: "Path"
) -> None:
    """Test rdflib with `base_iri`.

    Parameters:
        get_ontology_path: Fixture from `conftest.py` to retrieve a
            `pathlib.Path` object pointing to an ontology test file.
        tmp_path: Built-in pytest fixture, which returns a `pathlib.Path`
            object representing a temporary folder.

    """
    pytest.importorskip("rdflib")
    import shutil

    from tripper.triplestore import RDF, Triplestore

    ontopath_family = get_ontology_path("family")
    tmp_onto = tmp_path / "family.ttl"
    shutil.copy(ontopath_family, tmp_onto)

    ts = Triplestore(backend="rdflib")
    FAM = ts.bind(  # pylint: disable=invalid-name
        "fam", "http://onto-ns.com/ontologies/examples/family#"
    )
    ts.add_triples(
        [
            (":Nils", RDF.type, FAM.Father),
            (":Anna", RDF.type, FAM.Dauther),
            (":Nils", FAM.hasChild, ":Anna"),
        ]
    )
    ts.close()


def test_backend_rdflib_graph(
    get_ontology_path: "Callable[[str], Path]",
) -> None:
    """Test rdflib backend, using the `graph` keyword argument to expose an
    existing rdflib graph with tripper."""
    pytest.importorskip("rdflib")
    from rdflib import Graph, URIRef

    from tripper import RDF, RDFS, Triplestore

    graph = Graph()
    graph.parse(source=get_ontology_path("family"))

    # Test that triples from the original graph are available via tripper
    ts = Triplestore(backend="rdflib", graph=graph)
    FAM = ts.bind("fam", "http://onto-ns.com/ontologies/examples/family#")
    assert ts.value(FAM.Father, RDFS.subClassOf) == FAM.Person
    assert ts.value(FAM.Dauther, RDFS.subClassOf) == FAM.Person

    # Test that triples added with tripper are available in the original
    # graph
    ts.add_triples([(":Nils", RDF.type, FAM.Father)])
    assert graph.value(URIRef(":Nils"), URIRef(RDF.type)) == URIRef(FAM.Father)
