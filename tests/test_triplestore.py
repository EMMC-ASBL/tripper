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


# @pytest.mark.parametrize("backend", ["ontopy", "rdflib"])
@pytest.mark.parametrize("backend", ["rdflib"])
def test_triplestore(
    backend: str,
    example_function: "Callable[[Any, Any], Any]",
    expected_function_triplestore: str,
) -> None:
    """Test the Triplestore class."""
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
    )

    ts_as_turtle = store.serialize(format="turtle")
    assert ts_as_turtle == expected_function_triplestore


def test_backend_rdflib(expected_function_triplestore: str) -> None:
    """Specifically test the rdflib backend Triplestore."""
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


def test_backend_ontopy(get_ontology_path: "Callable[[str], Path]") -> None:
    """Specifically test the ontopy backend Triplestore."""
    from tripper.triplestore import Namespace, Triplestore

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
