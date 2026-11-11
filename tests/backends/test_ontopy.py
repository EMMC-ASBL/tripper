"""Test ontopy backend."""

from typing import TYPE_CHECKING

import pytest

from tripper import Namespace, Triplestore

if TYPE_CHECKING:  # pragma: no cover
    from collections.abc import Callable
    from pathlib import Path


@pytest.mark.filterwarnings("ignore:adding new IRI to ontology:UserWarning")
def test_backend_ontopy(get_ontology_path: "Callable[[str], Path]") -> None:
    """Specifically test the ontopy backend Triplestore.

    Parameters:
        get_ontology_path: Fixture from `conftest.py` to retrieve a
            `pathlib.Path` object pointing to an ontology test file.

    """
    pytest.importorskip("ontopy")
    ontopath_food = get_ontology_path("food")

    FOOD = Namespace(
        "http://onto-ns.com/ontologies/examples/food#",
        label_annotations=True,
        check=True,
        triplestore=ontopath_food,
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
