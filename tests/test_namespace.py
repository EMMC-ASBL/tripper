"""Test namespaces."""

# pylint: disable=invalid-name,duplicate-code
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pathlib import Path
    from typing import Callable


# if True:
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

    # Save and reuse the cache
    FOOD2._save_cache()  # pylint: disable=protected-access
    FOOD3 = Namespace(
        "http://onto-ns.com/ontologies/examples/food#", check=True
    )
    assert FOOD3[name] == FOOD3 + name
    assert FOOD3.Vegetable == FOOD3 + name
    with pytest.raises(NoSuchIRIError):
        FOOD3.NonExisting  # pylint: disable=pointless-statement


# if True:
def test_triplestore_arg() -> None:
    """Test triplestore argument of Namespace.__init__()."""
    pytest.importorskip("rdflib")
    from tripper import RDF, Namespace, Triplestore
    from tripper.errors import NamespaceError, NoSuchIRIError
    from tripper.testutils import ontodir

    assert str(RDF) == "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
    assert RDF.type == "http://www.w3.org/1999/02/22-rdf-syntax-ns#type"

    ts = Triplestore("rdflib")
    ts.parse(ontodir / "family.ttl")

    FAM = Namespace(
        "http://onto-ns.com/ontologies/examples/family#",
        check=True,
        triplestore=ts,
    )
    assert FAM.Son == "http://onto-ns.com/ontologies/examples/family#Son"
    assert FAM["Son"] == "http://onto-ns.com/ontologies/examples/family#Son"
    assert FAM + "Son" == "http://onto-ns.com/ontologies/examples/family#Son"
    with pytest.raises(NoSuchIRIError):
        FAM.NonExisting  # pylint: disable=pointless-statement

    with pytest.raises(NamespaceError):
        Namespace("http://example.com", check=True, triplestore=Ellipsis)


# if True:
def test_namespace_emmo():
    """Test EMMO"""
    pytest.importorskip("rdflib")
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
