"""Test collection."""

import pytest


def test_collection():
    """Test if we can use a DLite collection as backend."""
    dlite = pytest.importorskip("dlite")  # pylint: disable=unused-variable
    from tripper import DM, EMMO, MAP, XSD, Literal, Triplestore
    from tripper.utils import en

    ts = Triplestore(backend="collection")
    assert not list(ts.triples())

    STRUCTURE = ts.bind(  # pylint: disable=invalid-name
        "structure", "http://onto-ns.com/meta/0.1/Structure#"
    )
    CIF = ts.bind(  # pylint: disable=invalid-name
        "cif", "http://emmo.info/0.1/cif-ontology#"
    )
    triples = [
        (STRUCTURE.name, DM.hasLabel, en("Strontium titanate")),
        (STRUCTURE.masses, DM.hasUnit, Literal("u", datatype=XSD.string)),
        (STRUCTURE.symbols, MAP.mapsTo, EMMO.Symbol),
        (STRUCTURE.positions, MAP.mapsTo, EMMO.PositionVector),
        (STRUCTURE.cell, MAP.mapsTo, CIF.cell),
        (STRUCTURE.masses, MAP.mapsTo, EMMO.Mass),
    ]

    ts.add_triples(triples)

    assert set(ts.triples()) == set(triples)

    ts.remove(object=EMMO.Mass)
    assert set(ts.triples()) == set(triples[:-1])

    # Test that we can initialise from an existing collection
    coll = dlite.Collection()
    coll.add_relation(STRUCTURE.name, DM.hasLabel, "Strontium titanate", "@en")
    coll.add_relation(STRUCTURE.masses, DM.hasUnit, "u", XSD.string)
    for triple in triples[2:]:
        coll.add_relation(*triple)
    ts2 = Triplestore(backend="collection", collection=coll)
    assert set(ts2.triples()) == set(triples)

    # Test serialising/parsing
    dump = ts.serialize()
    ts3 = Triplestore(backend="collection")
    ts3.parse(data=dump)
    assert set(ts3.triples()) == set(ts.triples())
    label = ts3.value(STRUCTURE.name, DM.hasLabel)
    assert isinstance(label, Literal)
    assert label == Literal("Strontium titanate", lang="en")
