#!/usr/bin/env python
"""Test mappings."""

import pytest


def test_mappings():
    """Test mappings.
    Uses rdflib as backend
    """

    pytest.importorskip("rdflib")

    from tripper import Triplestore
    from tripper.mappings import mapping_routes

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
        sources={MOL.groundstate_energy: 1.0},
        triplestore=ts,
    )

    assert routes.number_of_routes() == 1
    assert routes.output_iri == (
        "http://onto-ns.com/meta/0.1/Substance#molecule_energy"
    )
    assert routes.cost == 2.0
    assert (
        routes.visualise(0).strip()
        == """
digraph G {
  "mol:groundstate_energy" -> "chem:GroundStateEnergy" [label="mapsTo"];
  "chem:GroundStateEnergy" -> "sub:molecule_energy" [label="inverse(mapsTo)"];
}
""".strip()
    )

    # Commented out, to avoid dependencies of Graphviz
    # routes.visualise(0, output="graph.png", format="png", dot="dot")


def test_value_repr():
    """Test Value.__repr__()."""
    from tripper.mappings import Value

    assert repr(Value(3.0, iri="ex:a")) == "Value(3.0, iri=ex:a)"
    assert repr(
        Value(3.0, unit="m", iri="ex:a", property_iri="ex:length", cost=2.0)
    ) == ("Value(3.0, unit=m, iri=ex:a, property_iri=ex:length, cost=2.0)")


def test_value_show():
    """Test Value.show()."""
    from tripper.mappings import Value

    value = Value(3.0, unit="m", iri="ex:a", cost=2.0)
    assert value.show(name="x", indent=2) == (
        "  x:\n"
        "    iri: ex:a\n"
        "    property_iri: None\n"
        "    unit: m\n"
        "    cost: 2.0\n"
        "    value: 3.0"
    )


def _example_steps():
    """Return mapping steps for the examples in the tests below.

    The step "ex:c" has two routes, one from each of the values "ex:a"
    and "ex:b".  The step "ex:d" has one input, "ex:c":

        ex:a (cost 1) --.
                         >-- ex:c (cost 10) --> ex:d (cost 1)
        ex:b (cost 2) --'
    """
    from tripper.mappings import MappingStep, Value

    a = Value(1.0, iri="ex:a", cost=1.0)
    b = Value(2.0, iri="ex:b", cost=2.0)

    c = MappingStep("ex:c", cost=10.0)
    c.add_input(a, name="x")
    c.add_input(b, name="x")

    d = MappingStep("ex:d", cost=1.0)
    d.add_input(c, name="y")

    return a, b, c, d


def test_lowest_costs():
    """Test MappingStep.lowest_costs()."""
    pytest.importorskip("numpy")
    from tripper.mappings import MappingStep

    a, b, c, d = _example_steps()

    # Each route costs the cost of its input plus the cost of the step:
    # route 0: 1 + 10 = 11 and route 1: 2 + 10 = 12
    assert c.lowest_costs() == [(11.0, 0), (12.0, 1)]
    assert c.lowest_costs(nresults=1) == [(11.0, 0)]

    # The costs add up through several steps
    assert d.lowest_costs() == [(12.0, 0), (13.0, 1)]

    # The cost of a step may be a function of the triplestore and the
    # IRIs of the input and output.  Here it is the number of inputs.
    def cost(triplestore, input_iris, output_iri):
        return len(input_iris)

    e = MappingStep("ex:e", cost=cost)
    e.add_inputs({"x": a, "y": b})
    assert e.lowest_costs() == [(1.0 + 2.0 + 2, 0)]


def test_mappingstep_show():
    """Test MappingStep.show()."""
    a, b, c, d = _example_steps()

    # Show all routes
    assert d.show() == (
        "Step:\n"
        "  steptype: UNSPECIFIED\n"
        "  output_iri: ex:d\n"
        "  output_unit: None\n"
        "  cost: 1.0\n"
        "  routes:\n"
        "    - y:\n"
        "        steptype: UNSPECIFIED\n"
        "        output_iri: ex:c\n"
        "        output_unit: None\n"
        "        cost: 10.0\n"
        "        routes:\n"
        "          - x:\n"
        "              iri: ex:a\n"
        "              property_iri: None\n"
        "              unit: None\n"
        "              cost: 1.0\n"
        "              value: 1.0\n"
        "          - x:\n"
        "              iri: ex:b\n"
        "              property_iri: None\n"
        "              unit: None\n"
        "              cost: 2.0\n"
        "              value: 2.0"
    )

    # Show only route number 1, i.e. the route from ex:b
    assert c.show(routeno=1) == (
        "Step:\n"
        "  steptype: UNSPECIFIED\n"
        "  output_iri: ex:c\n"
        "  output_unit: None\n"
        "  cost: 10.0\n"
        "  inputs:\n"
        "    - x:\n"
        "        iri: ex:b\n"
        "        property_iri: None\n"
        "        unit: None\n"
        "        cost: 2.0\n"
        "        value: 2.0"
    )
