"""Test cost."""


def test_cost():
    """Test cost"""

    import pytest

    pytest.importorskip("rdflib")

    from tripper import Triplestore

    ts = Triplestore(backend="rdflib")

    # Define some prefixed namespaces
    CHEM = ts.bind("chem", "http://onto-ns.com/onto/chemistry#")
    MOL = ts.bind("mol", "http://onto-ns.com/meta/0.1/Molecule#")
    SUB = ts.bind("sub", "http://onto-ns.com/meta/0.1/Substance#")

    def formula_cost(ts, input_iris, output_iri):
        """Returns a cost."""
        return 2.72

    # Add mappings from data models to ontology
    ts.map(MOL.name, CHEM.Identifier, cost=3.14)
    ts.map(SUB.formula, CHEM.Formula, cost=formula_cost)

    assert ts._get_cost(CHEM.Identifier) == 3.14
    assert ts._get_cost(CHEM.Formula) == 2.72
