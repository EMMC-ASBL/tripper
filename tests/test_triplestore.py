"""Test triplestore.

If backend is given, only that backend will be tested.  Otherwise all
installed backends are tested one by one.
"""

# pylint: disable=duplicate-code,comparison-with-callable,invalid-name
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pathlib import Path
    from typing import Any, Callable


# @pytest.mark.parametrize("backend", ["rdflib", "ontopy", "collection"])
@pytest.mark.parametrize("backend", ["rdflib", "collection"])
def test_triplestore(  # pylint: disable=too-many-locals
    backend: str,
    example_function: "Callable[[Any, Any], Any]",
    expected_function_triplestore: str,
) -> None:
    """Test the Triplestore class.

    Parameters:
        backend: Dynamic parameter based on the parametrize decorator.
        example_function: Fixture from `conftest.py` to return a function
            implementation example for use with Triplestore.
        expected_function_triplestore: Fixture from `conftest.py`, which
            returns a Turtle-serialized string of what is expected when
            serializing the Triplestore in this test.

    """
    pytest.importorskip("rdflib")
    pytest.importorskip("dlite")
    pytest.importorskip("SPARQLWrapper")
    from tripper.triplestore import DCTERMS, OWL, RDF, RDFS, XSD, Triplestore

    ts = Triplestore(backend)
    assert ts.expand_iri("xsd:integer") == XSD.integer
    assert ts.prefix_iri(RDF.type) == "rdf:type"
    EX = ts.bind(
        "ex", "http://example.com/onto#"
    )  # pylint: disable=invalid-name
    assert str(EX) == "http://example.com/onto#"
    ts.add_mapsTo(
        EX.MyConcept, "http://onto-ns.com/meta/0.1/MyEntity", "myprop"
    )
    ts.add((EX.MyConcept, RDFS.subClassOf, OWL.Thing))
    ts.add((EX.AnotherConcept, RDFS.subClassOf, OWL.Thing))
    ts.add((EX.Sum, RDFS.subClassOf, OWL.Thing))
    assert ts.has(EX.Sum) is True
    assert ts.has(EX.Sum, RDFS.subClassOf, OWL.Thing) is True
    assert ts.has(object=EX.NotInOntology) is False

    func_iri = ts.add_function(
        example_function,
        expects=(EX.MyConcept, EX.AnotherConcept),
        returns=EX.Sum,
        base_iri=EX,
        standard="fno",
    )

    ts_as_turtle = ts.serialize(format="turtle")
    assert ts_as_turtle == expected_function_triplestore

    # Test SPARQL query
    try:
        rows = ts.query("SELECT ?s ?o WHERE { ?s rdfs:subClassOf ?o }")
    except NotImplementedError:
        pass
    else:
        assert len(rows) == 3
        rows.sort()  # ensure consistent ordering of rows
        assert rows[0] == (
            "http://example.com/onto#AnotherConcept",
            "http://www.w3.org/2002/07/owl#Thing",
        )
        assert rows[1] == (
            "http://example.com/onto#MyConcept",
            "http://www.w3.org/2002/07/owl#Thing",
        )
        assert rows[2] == (
            "http://example.com/onto#Sum",
            "http://www.w3.org/2002/07/owl#Thing",
        )

    # Test value() method
    assert ts.value(func_iri, DCTERMS.description) == example_function.__doc__
    # assert ts.value(
    #     func_iri, DCTERMS.description, lang="en"
    # ) == example_function.__doc__
    assert ts.value(func_iri, DCTERMS.description, lang="de") is None


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
    assert list(ts.function_repo.values())[0] == cost

    def func(parameter):
        return parameter + 1

    ts.add_function(func, expects=EX.Sum, returns=EX.OneMore, cost=cost)
    assert list(ts.function_repo.values())[1] == func
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


@pytest.mark.filterwarnings("ignore:adding new IRI to ontology:UserWarning")
def test_backend_ontopy(get_ontology_path: "Callable[[str], Path]") -> None:
    """Specifically test the ontopy backend Triplestore.

    Parameters:
        get_ontology_path: Fixture from `conftest.py` to retrieve a
            `pathlib.Path` object pointing to an ontology test file.

    """
    from tripper import Namespace, Triplestore

    pytest.importorskip("ontopy")
    ontopath_food = get_ontology_path("food")

    FOOD = Namespace(  # pylint: disable=invalid-name
        "http://onto-ns.com/ontologies/examples/food#",
        label_annotations=True,
        check=True,
        triplestore_url=ontopath_food,
    )

    ts = Triplestore(
        "ontopy",
        base_iri="http://onto-ns.com/ontologies/examples/food",
    )
    ts.parse(ontopath_food)

    ts = Triplestore(
        "ontopy",
        base_iri="http://onto-ns.com/ontologies/examples/food",
    )
    ts.bind("food", FOOD)
    with open(ontopath_food, "rt", encoding="utf8") as handle:
        ts.parse(data=handle.read())


def test_backend_sparqlwrapper() -> None:
    """Specifically test the SPARQLWrapper backend Triplestore."""
    from tripper import SKOS, Triplestore

    pytest.importorskip("SPARQLWrapper")
    ts = Triplestore(
        backend="sparqlwrapper",
        base_iri="http://vocabs.ardc.edu.au/repository/api/sparql/"
        "csiro_international-chronostratigraphic-chart_geologic-"
        "time-scale-2020",
    )
    with pytest.warns(UserWarning, match="unknown datatype"):
        for s, p, o in ts.triples(predicate=SKOS.notation):
            assert s
            assert p
            assert o


@pytest.mark.skip(
    "These will fail because we do not have credentials to modify the "
    "triplestore"
)
def test_backend_sparqlwrapper_methods() -> None:
    """Test SPARQLWrapper methods."""
    from tripper import RDFS, SKOS, Literal, Namespace, Triplestore

    ts = Triplestore(
        backend="sparqlwrapper",
        base_iri="http://vocabs.ardc.edu.au/repository/api/sparql/"
        "csiro_international-chronostratigraphic-chart_geologic-"
        "time-scale-2020",
    )

    ts.remove((None, SKOS.notation, None))

    EX = Namespace("http://example.com#")  # pylint: disable=invalid-name
    ts.add_triples(
        [
            (EX.a, RDFS.subClassOf, EX.base),
            (EX.a, SKOS.prefLabel, Literal("An a class.", lang="en")),
        ]
    )


def test_find_literal_triples() -> None:
    """Test finding literals."""
    pytest.importorskip("rdflib")

    from tripper import RDF, XSD, Literal, Triplestore
    from tripper.testutils import ontodir

    ts = Triplestore("rdflib")
    FAM = ts.bind("ex", "http://onto-ns.com/ontologies/examples/family#")
    ts.parse(ontodir / "family.ttl")
    ts.add_triples(
        [
            (FAM.Ola, RDF.type, FAM.Son),
            (FAM.Ola, FAM.hasName, Literal("Ola")),
            (FAM.Ola, FAM.hasAge, Literal(18)),
            (FAM.Ola, FAM.hasWeight, Literal(68.5)),
            (FAM.Kari, RDF.type, FAM.Dauther),
            (FAM.Kari, FAM.hasName, Literal("Kari")),
            (FAM.Kari, FAM.hasAge, Literal(18)),
            (FAM.Kari, FAM.hasWeight, Literal(66.2)),
            (FAM.Per, RDF.type, FAM.Father),
            (FAM.Per, FAM.hasName, Literal("Per")),
            (FAM.Per, FAM.hasAge, Literal(49)),
            (FAM.Per, FAM.hasWeight, Literal(83.8)),
            (FAM.Per, FAM.hasChild, FAM.Ola),
            (FAM.Per, FAM.hasChild, FAM.Kari),
        ]
    )
    assert set(
        ts.subjects(
            predicate=FAM.hasAge,
            object=Literal(18, datatype=XSD.integer),
        )
    ) == set([FAM.Ola, FAM.Kari])

    assert set(
        ts.triples(predicate=FAM.hasName, object=Literal("Per"))
    ) == set(
        [
            (FAM.Per, FAM.hasName, Literal("Per")),
        ]
    )
