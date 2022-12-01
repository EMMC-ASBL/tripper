"""Test collection."""
from tripper import EMMO, MAP, Triplestore

ts = Triplestore(backend="collection")
assert not list(ts.triples((None, None, None)))

STRUCTURE = ts.bind("structure", "http://onto-ns.com/meta/0.1/Structure#")
CIF = ts.bind("cif", "http://emmo.info/cif-ontology/0.1#")
triples = [
    (STRUCTURE.symbols, MAP.mapsTo, EMMO.Symbol),
    (STRUCTURE.positions, MAP.mapsTo, EMMO.PositionVector),
    (STRUCTURE.cell, MAP.mapsTo, CIF.cell),
    (STRUCTURE.masses, MAP.mapsTo, EMMO.Mass),
]

ts.add_triples(triples)
assert set(ts.triples((None, None, None))) == set(triples)

ts.remove((None, None, EMMO.Mass))
assert set(ts.triples((None, None, None))) == set(triples[:-1])
