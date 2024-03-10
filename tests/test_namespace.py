"""Test namespaces."""

# pylint: disable=invalid-name,duplicate-code
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pathlib import Path
    from typing import Callable


def test_namespaces() -> None:
    """Test namespaces."""
    pytest.importorskip("rdflib")
    from tripper import RDF, Namespace
    from tripper.errors import NoSuchIRIError
    from tripper.testutils import ontodir

    assert str(RDF) == "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
    assert RDF.type == "http://www.w3.org/1999/02/22-rdf-syntax-ns#type"

    FAM = Namespace(
        "http://onto-ns.com/ontologies/examples/family#",
        check=True,
        triplestore=ontodir / "family.ttl",
    )
    FOOD = Namespace(
        "http://onto-ns.com/ontologies/examples/food#",
        label_annotations=True,
        check=True,
        triplestore=ontodir / "food.ttl",
    )
    FOOD2 = Namespace(
        "http://onto-ns.com/ontologies/examples/food#",
        label_annotations=True,
        check=False,
        triplestore=ontodir / "food.ttl",
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


# if True:
def test_namespace_emmmo():
    """Test EMMO"""
    from tripper import Namespace
    from tripper.errors import NoSuchIRIError

    EMMO = Namespace(
        iri="https://w3id.org/emmo#",
        label_annotations=True,
        check=True,
    )
    assert EMMO.Atom == (
        "https://w3id.org/emmo#EMMO_eb77076b_a104_42ac_a065_798b2d2809ad"
    )
    with pytest.raises(NoSuchIRIError):
        EMMO.NonExisting  # pylint: disable=pointless-statement
