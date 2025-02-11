"""Test the tripper.units module."""


def test_get_emmo_triplestore():
    """Test get_emmo_triplestore()."""
    from tripper import EMMO, units

    ts = units.get_emmo_triplestore()
    assert ts.has(EMMO.Atom)


def test_emmo_namespace():
    """Test get_emmo_namespace()."""
    from tripper import EMMO, units

    ns = units.get_emmo_namespace()
    assert ns.Atom == EMMO.Atom


def test_get_unit_symbol():
    """Test get_unit_symbol()."""
    from tripper import EMMO, units

    assert units.get_unit_symbol(EMMO.Ampere) == "A"
    assert units.get_unit_symbol(EMMO.Kilogram) == "kg"
    assert units.get_unit_symbol(EMMO.Day) == "d"


def test_get_unit_iri():
    """Test get_unit_iri()."""
    from tripper import EMMO, units

    assert units.get_unit_iri("K") == EMMO.Kelvin
    assert units.get_unit_iri("cm") == EMMO.CentiMetre
    assert units.get_unit_iri("d") == EMMO.Day


if True:
#def test_extend_emmo_ureg():
    """Test extend_emmo_ureg()."""
    from tripper.units import Units

    units = Units()
