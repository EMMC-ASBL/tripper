"""Test collection."""
import dlite

from tripper import EMMO, MAP, Triplestore

ts = Triplestore(backend="collection")
assert not list(ts.triples())

STRUCTURE = ts.bind("structure", "http://onto-ns.com/meta/0.1/Structure#")
CIF = ts.bind("cif", "http://emmo.info/0.1/cif-ontology#")
triples = [
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
for triple in triples:
    coll.add_relation(*triple)
ts2 = Triplestore(backend="collection", collection=coll)
assert set(ts2.triples()) == set(triples)
