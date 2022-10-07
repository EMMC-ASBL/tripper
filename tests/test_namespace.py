"""Test namespaces"""
# pylint: disable=invalid-name
from pathlib import Path

import pytest
from triplestore import RDF, Namespace, Triplestore, en
from triplestore.triplestore import NoSuchIRIError, function_id

thisdir = Path(__file__).absolute().parent
ontopath_family = thisdir / "ontologies" / "family.ttl"
ontopath_food = thisdir / "ontologies" / "food.ttl"


# Test namespaces
# ---------------
assert str(RDF) == "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
assert RDF.type == "http://www.w3.org/1999/02/22-rdf-syntax-ns#type"

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
