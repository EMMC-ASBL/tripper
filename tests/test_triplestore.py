"""Test triplestore.

If backend is given, only that backend will be tested.  Otherwise all
installed backends are tested one by one.
"""
# pylint: disable=duplicate-code,comparison-with-callable
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pathlib import Path
    from typing import Any, Callable


# @pytest.mark.parametrize("backend", ["rdflib", "ontopy", "collection"])
@pytest.mark.parametrize("backend", ["rdflib", "collection"])
def test_triplestore(
    backend: str,
    example_function: "Callable[[Any, Any], Any]",
    expected_function_triplestore: str,
) -> None:
    """Test the Triplestore class.

    Parameters:
        backend: Dynamic parameter based on the parametrize decorator.
        example_function: Fixture from `conftest.py` to return a function
            implementation example for use with Triplestore.
        expected_function_triplestore: Fixture from `conftest.py`, which returns a
            Turtle-serialized string of what is expected when serializing the
            Triplestore in this test.

    """
    from tripper.triplestore import OWL, RDF, RDFS, XSD, Triplestore

    store = Triplestore(backend)
    assert store.expand_iri("xsd:integer") == XSD.integer
    assert store.prefix_iri(RDF.type) == "rdf:type"
    EX = store.bind("ex", "http://example.com/onto#")  # pylint: disable=invalid-name
    assert str(EX) == "http://example.com/onto#"
    store.add_mapsTo(EX.MyConcept, "http://onto-ns.com/meta/0.1/MyEntity", "myprop")
    store.add((EX.MyConcept, RDFS.subClassOf, OWL.Thing))
    store.add((EX.AnotherConcept, RDFS.subClassOf, OWL.Thing))
    store.add((EX.Sum, RDFS.subClassOf, OWL.Thing))
    assert store.has(EX.Sum) is True
    assert store.has(EX.Sum, RDFS.subClassOf, OWL.Thing) is True
    assert store.has(object=EX.NotInOntology) is False

    store.add_function(
        example_function,
        expects=(EX.MyConcept, EX.AnotherConcept),
        returns=EX.Sum,
        base_iri=EX,
        standard="fno",
    )

    try:
        ts_as_turtle = store.serialize(format="turtle")
    except NotImplementedError:
        pass
    else:
        assert ts_as_turtle == expected_function_triplestore

    # Test SPARQL query
    try:
        rows = store.query("SELECT ?s ?o WHERE { ?s rdfs:subClassOf ?o }")
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


def test_backend_rdflib(expected_function_triplestore: str) -> None:
    """Specifically test the rdflib backend Triplestore.

    Parameters:
        expected_function_triplestore: Fixture from `conftest.py`, which returns a
            Turtle-serialized string of what is expected when serializing the
            Triplestore in this test.

    """
    from tripper.triplestore import RDFS, Triplestore

    store = Triplestore("rdflib")
    EX = store.bind("ex", "http://example.com/onto#")  # pylint: disable=invalid-name
    store.parse(format="turtle", data=expected_function_triplestore)
    assert store.serialize(format="turtle") == expected_function_triplestore
    store.set((EX.AnotherConcept, RDFS.subClassOf, EX.MyConcept))

    def cost(parameter):
        return 2 * parameter

    store.add_mapsTo(EX.Sum, "http://onto-ns.com/meta/0.1/MyEntity#sum", cost=cost)
    assert list(store.function_repo.values())[0] == cost

    def func(parameter):
        return parameter + 1

    store.add_function(func, expects=EX.Sum, returns=EX.OneMore, cost=cost)
    assert list(store.function_repo.values())[1] == func
    assert len(store.function_repo) == 2  # cost is only added once

    def func2(parameter):
        return parameter + 2

    def cost2(parameter):
        return 2 * parameter + 1

    store.add_function(func2, expects=EX.Sum, returns=EX.EvenMore, cost=cost2)
    assert len(store.function_repo) == 4


def test_backend_rdflib_base_iri(
    get_ontology_path: "Callable[[str], Path]", tmp_path: "Path"
) -> None:
    """Test rdflib with `base_iri`.

    Parameters:
        get_ontology_path: Fixture from `conftest.py` to retrieve a `pathlib.Path`
            object pointing to an ontology test file.
        tmp_path: Built-in pytest fixture, which returns a `pathlib.Path` object
            representing a temporary folder.

    """
    import shutil

    from tripper.triplestore import RDF, Triplestore

    ontopath_family = get_ontology_path("family")
    tmp_onto = tmp_path / "family.ttl"
    shutil.copy(ontopath_family, tmp_onto)

    store = Triplestore(backend="rdflib", base_iri=f"file://{tmp_onto}")
    FAM = store.bind(  # pylint: disable=invalid-name
        "fam", "http://onto-ns.com/ontologies/examples/family#"
    )
    store.add_triples(
        [
            (":Nils", RDF.type, FAM.Father),
            (":Anna", RDF.type, FAM.Dauther),
            (":Nils", FAM.hasChild, ":Anna"),
        ]
    )
    store.close()


def test_backend_ontopy(get_ontology_path: "Callable[[str], Path]") -> None:
    """Specifically test the ontopy backend Triplestore.

    Parameters:
        get_ontology_path: Fixture from `conftest.py` to retrieve a `pathlib.Path`
            object pointing to an ontology test file.

    """
    from tripper import Namespace, Triplestore

    ontopath_food = get_ontology_path("food")

    FOOD = Namespace(  # pylint: disable=invalid-name
        "http://onto-ns.com/ontologies/examples/food#",
        label_annotations=True,
        check=True,
        triplestore_url=ontopath_food,
    )

    store = Triplestore(
        "ontopy",
        base_iri="http://onto-ns.com/ontologies/examples/food",
    )
    store.parse(ontopath_food)

    store = Triplestore(
        "ontopy",
        base_iri="http://onto-ns.com/ontologies/examples/food",
    )
    store.bind("food", FOOD)
    with open(ontopath_food, "rt", encoding="utf8") as handle:
        store.parse(data=handle.read())


def test_backend_sparqlwrapper() -> None:
    """Specifically test the SPARQLWrapper backend Triplestore."""
    from tripper import SKOS, Triplestore

    store = Triplestore(
        backend="sparqlwrapper",
        base_iri="http://vocabs.ardc.edu.au/repository/api/sparql/"
        "csiro_international-chronostratigraphic-chart_geologic-time-scale-2020",
    )
    for s, p, o in store.triples((None, SKOS.notation, None)):
        assert s
        assert p
        assert o


@pytest.mark.skip(
    "These will fail because we do not have credentials to modify the triplestore"
)
def test_backend_sparqlwrapper_methods() -> None:
    """Test SPARQLWrapper methods."""
    from tripper import RDFS, SKOS, Literal, Namespace, Triplestore

    store = Triplestore(
        backend="sparqlwrapper",
        base_iri="http://vocabs.ardc.edu.au/repository/api/sparql/"
        "csiro_international-chronostratigraphic-chart_geologic-time-scale-2020",
    )

    store.remove((None, SKOS.notation, None))

    EX = Namespace("http://example.com#")  # pylint: disable=invalid-name
    store.add_triples(
        [
            (EX.a, RDFS.subClassOf, EX.base),
            (EX.a, SKOS.prefLabel, Literal("An a class.", lang="en")),
        ]
    )
