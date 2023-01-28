#!/usr/bin/env python
"""Test mappings."""
from pathlib import Path

from tripper import Triplestore
from tripper.mappings import mapping_routes

# Configure paths
thisdir = Path(__file__).parent.absolute()

ts = Triplestore(backend="rdflib")


# Define some prefixed namespaces
CHEM = ts.bind("chem", "http://onto-ns.com/onto/chemistry#")
MOL = ts.bind("mol", "http://onto-ns.com/meta/0.1/Molecule#")
MOL2 = ts.bind("mol2", "http://onto-ns.com/meta/0.1/Molecule2#")
SUB = ts.bind("sub", "http://onto-ns.com/meta/0.1/Substance#")


# Add mappings from data models to ontology
ts.add_mapsTo(CHEM.Identifier, MOL.name)
ts.add_mapsTo(CHEM.Identifier, SUB.id)

ts.add_mapsTo(CHEM.GroundStateEnergy, MOL.groundstate_energy)
ts.add_mapsTo(CHEM.GroundStateEnergy, MOL2.energy)
ts.add_mapsTo(CHEM.GroundStateEnergy, SUB.molecule_energy)


routes = mapping_routes(
    target=SUB.molecule_energy,
    sources={},  # MOL.groundstate_energy: 1.0},
    triplestore=ts,
)

assert routes.number_of_routes() == 0
assert routes.output_iri == ("http://onto-ns.com/meta/0.1/Substance#molecule_energy")
assert routes.cost == 2.0
assert (
    routes.show()
    == """\
Step:
  steptype: MAPSTO
  output_iri: http://onto-ns.com/meta/0.1/Substance#molecule_energy
  output_unit: None
  cost: 2.0
  routes:
    - arg1:
        steptype: INV_MAPSTO
        output_iri: http://onto-ns.com/onto/chemistry#GroundStateEnergy
        output_unit: None
        cost: 2.0
        routes:
          - arg1:
              steptype: UNSPECIFIED
              output_iri: http://onto-ns.com/meta/0.1/Molecule#groundstate_energy
              output_unit: None
              cost: 1.0
              routes:
          - arg1:
              steptype: UNSPECIFIED
              output_iri: http://onto-ns.com/meta/0.1/Molecule2#energy
              output_unit: None
              cost: 1.0
              routes:\
"""
)
