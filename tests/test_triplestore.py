"""Test triplestore.

If backend is given, only that backend will be tested.  Otherwise all
installed backends are tested one by one.
"""
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pathlib import Path
    from typing import Any, Callable


@pytest.mark.parametrize("backend", ["ontopy", "rdflib"])
def test_triplestore(backend: str, example_function: "Callable[[Any, Any], Any]", expected_function_triplestore: str) -> None:
    """Test the Triplestore class."""
    from tripper.triplestore import OWL, RDF, RDFS, XSD, Triplestore

    ts = Triplestore(backend)
    assert ts.expand_iri("xsd:integer") == XSD.integer
    assert ts.prefix_iri(RDF.type) == "rdf:type"
    EX = ts.bind("ex", "http://example.com/onto#")
    assert str(EX) == "http://example.com/onto#"
    ts.add_mapsTo(EX.MyConcept, "http://onto-ns.com/meta/0.1/MyEntity", "myprop")
    ts.add((EX.MyConcept, RDFS.subClassOf, OWL.Thing))
    ts.add((EX.AnotherConcept, RDFS.subClassOf, OWL.Thing))
    ts.add((EX.Sum, RDFS.subClassOf, OWL.Thing))
    assert ts.has(EX.Sum) == True
    assert ts.has(EX.Sum, RDFS.subClassOf, OWL.Thing) == True
    assert ts.has(object=EX.NotInOntology) == False


    ts.add_function(
        example_function, expects=(EX.MyConcept, EX.AnotherConcept), returns=EX.Sum, base_iri=EX
    )

    ts_as_turtle = ts.serialize(format="turtle")
    assert ts_as_turtle == expected_function_triplestore


def test_backend_rdflib(expected_function_triplestore: str) -> None:
    """Specifically test the rdflib backend Triplestore."""
    from tripper.triplestore import RDFS, Triplestore

    ts2 = Triplestore("rdflib")
    EX = ts2.bind("ex", "http://example.com/onto#")
    ts2.parse(format="turtle", data=expected_function_triplestore)
    assert ts2.serialize(format="turtle") == expected_function_triplestore
    ts2.set((EX.AnotherConcept, RDFS.subClassOf, EX.MyConcept))


    def cost(x):
        return 2 * x


    ts2.add_mapsTo(EX.Sum, "http://onto-ns.com/meta/0.1/MyEntity#sum", cost=cost)
    assert list(ts2.function_repo.values())[0] == cost


    def func(x):
        return x + 1


    ts2.add_function(func, expects=EX.Sum, returns=EX.OneMore, cost=cost)
    assert list(ts2.function_repo.values())[1] == func
    assert len(ts2.function_repo) == 2  # cost is only added once


    def func2(x):
        return x + 2


    def cost2(x):
        return 2 * x + 1


    ts2.add_function(func2, expects=EX.Sum, returns=EX.EvenMore, cost=cost2)
    assert len(ts2.function_repo) == 4


def test_backend_ontopy(get_ontology_path: "Callable[[str], Path]") -> None:
    """Specifically test the ontopy backend Triplestore."""
    from tripper.triplestore import Triplestore, Namespace

    ontopath_food = get_ontology_path("food")

    FOOD = Namespace(
        "http://onto-ns.com/ontologies/examples/food#",
        label_annotations=True,
        check=True,
        triplestore_url=ontopath_food,
    )

    ts4 = Triplestore(
        "ontopy", base_iri="http://onto-ns.com/ontologies/examples/food",
    )
    ts4.parse(ontopath_food)

    ts5 = Triplestore(
        "ontopy", base_iri="http://onto-ns.com/ontologies/examples/food",
    )
    ts5.bind('food', FOOD)
    with open(ontopath_food, 'rt') as f:
        ts5.parse(data=f.read())
