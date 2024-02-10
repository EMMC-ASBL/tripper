"""Test namespaces."""

# pylint: disable=invalid-name,duplicate-code
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pathlib import Path
    from typing import Callable


def test_namespaces(get_ontology_path: "Callable[[str], Path]") -> None:
    """Test namespaces.

    Parameters:
        get_ontology_path: Fixture from `conftest.py` to retrieve a
            `pathlib.Path` object pointing to an ontology test file.

    """
    pytest.importorskip("rdflib")
    from tripper import RDF, Namespace
    from tripper.errors import NoSuchIRIError

    assert str(RDF) == "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
    assert RDF.type == "http://www.w3.org/1999/02/22-rdf-syntax-ns#type"

    ontopath_family = get_ontology_path("family")
    ontopath_food = get_ontology_path("food")

    FAM = Namespace(
        "http://onto-ns.com/ontologies/examples/family#",
        check=True,
        triplestore_url=ontopath_family,
    )
    FOOD = Namespace(
        "http://onto-ns.com/ontologies/examples/food#",
        label_annotations=True,
        check=True,
        triplestore_url=ontopath_food,
    )
    FOOD2 = Namespace(
        "http://onto-ns.com/ontologies/examples/food#",
        label_annotations=True,
        check=False,
        triplestore_url=ontopath_food,
    )
    assert FAM.Son == "http://onto-ns.com/ontologies/examples/family#Son"
    assert FAM["Son"] == "http://onto-ns.com/ontologies/examples/family#Son"
    assert FAM + "Son" == "http://onto-ns.com/ontologies/examples/family#Son"

    name = "FOOD_345ecde3_3cac_41d2_aad6_cb6835a27b41"
    assert FOOD[name] == FOOD + name
    assert FOOD.Vegetable == FOOD + name

    assert FOOD2[name] == FOOD2 + name
    assert FOOD2.Vegetable == FOOD2 + name

    with pytest.raises(NoSuchIRIError):
        FAM.NonExisting  # pylint: disable=pointless-statement

    with pytest.raises(NoSuchIRIError):
        FOOD.NonExisting  # pylint: disable=pointless-statement

    assert FOOD2.NonExisting == FOOD2 + "NonExisting"
