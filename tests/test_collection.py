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


# TODO: Fix handling of Literal in Collections (Issue #160, PR #165) and reactivate test.
#    # Test that we can initialise from an existing collection
#    coll = dlite.Collection()
#    for triple in triples:
#        coll.add_relation(*triple)
#    ts2 = Triplestore(backend="collection", collection=coll)
#    assert set(ts2.triples()) == set(triples)
#
#    # Test serialising/parsing
#    dump = ts.serialize(backend="rdflib")
#    ts3 = Triplestore(backend="collection")
#    ts3.parse(backend="rdflib", data=dump)
#    assert set(ts3.triples()) == set(triples)
