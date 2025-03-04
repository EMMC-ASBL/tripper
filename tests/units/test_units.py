"""Test the tripper.units module."""

import sys

import pytest

pytest.importorskip("pint")
pytest.importorskip("rdflib")


def test_get_emmo_triplestore():
    """Test get_emmo_triplestore()."""
    from tripper import EMMO, units

    ts = units.units.get_emmo_triplestore()
    assert ts.has(EMMO.Atom)


def test_emmo_namespace():
    """Test get_emmo_namespace()."""
    from tripper import EMMO, units

    ns = units.units.get_emmo_namespace()
    assert ns.Atom == EMMO.Atom


def test_base_unit_expression():
    """Test base_unit_expression()."""
    from tripper.units.units import Dimension, base_unit_expression

    assert base_unit_expression(Dimension(1, 0, 0, 0, 0, 0, 0)) == "Second"
    assert base_unit_expression(Dimension(2, 0, 0, 0, 0, 0, 0)) == "Second**2"
    assert (
        base_unit_expression(Dimension(-2, 0, 1, 0, 0, 0, 0))
        == "Second**-2 * Kilogram"
    )


def test_units():
    """Test the Units class."""
    # pylint: disable=too-many-statements
    from tripper import EMMO
    from tripper.units import Units
    from tripper.units.units import Dimension

    units = Units()

    unit = units.get_unit(name="Ampere")
    assert unit.name == "Ampere"
    assert unit.aliases == []
    assert unit.symbols == ["A"]
    assert unit.dimension == Dimension(T=0, L=0, M=0, I=1, H=0, N=0, J=0)
    assert unit.emmoIRI == EMMO.Ampere
    assert unit.qudtIRI == "http://qudt.org/vocab/unit/A"
    assert unit.omIRI is None
    assert unit.ucumCodes == ["A"]
    assert unit.unitCode == "AMP"
    assert unit.multiplier is None
    assert unit.offset is None

    unit = units.get_unit(symbol="Pa")
    assert unit.name == "Pascal"
    assert unit.symbols == ["Pa"]
    assert unit.dimension == Dimension(T=-2, L=-1, M=1, I=0, H=0, N=0, J=0)
    assert unit.emmoIRI == EMMO.Pascal
    assert unit.qudtIRI == "http://qudt.org/vocab/unit/PA"
    assert unit.ucumCodes == ["Pa"]
    assert unit.unitCode == "PAL"

    unit = units.get_unit(iri=EMMO.Day)
    assert unit.name == "Day"
    assert unit.symbols == ["d"]
    assert unit.dimension == Dimension(T=1, L=0, M=0, I=0, H=0, N=0, J=0)
    assert unit.emmoIRI == EMMO.Day
    assert unit.qudtIRI == "http://qudt.org/vocab/unit/DAY"
    assert unit.ucumCodes == ["d"]
    assert unit.unitCode == "DAY"
    assert unit.multiplier == 86400.0
    assert unit.offset == 0.0

    unit = units.get_unit(iri="http://qudt.org/vocab/unit/L")
    assert unit.name == "Litre"
    assert unit.symbols == ["L"]
    assert unit.dimension == Dimension(T=0, L=3, M=0, I=0, H=0, N=0, J=0)
    assert unit.emmoIRI == EMMO.Litre
    assert unit.qudtIRI == "http://qudt.org/vocab/unit/L"
    assert unit.ucumCodes == ["L", "l"]
    assert unit.unitCode == "B51"
    assert unit.multiplier == 0.001
    assert unit.offset == 0.0

    unit = units.get_unit(iri=EMMO.Day)
    assert unit.name == "Day"
    assert unit.symbols == ["d"]
    assert unit.dimension == Dimension(T=1, L=0, M=0, I=0, H=0, N=0, J=0)
    assert unit.emmoIRI == EMMO.Day
    assert unit.qudtIRI == "http://qudt.org/vocab/unit/DAY"
    assert unit.ucumCodes == ["d"]
    assert unit.unitCode == "DAY"
    assert unit.multiplier == 86400.0
    assert unit.offset == 0.0

    unit = units.get_unit(unitCode="HUR")
    assert unit.name == "Hour"
    assert unit.symbols == ["h"]
    assert unit.dimension == Dimension(T=1, L=0, M=0, I=0, H=0, N=0, J=0)
    assert unit.multiplier == 3600.0
    assert unit.offset == 0.0


@pytest.mark.skipif(sys.version_info < (3, 9), reason="requires Python 3.9")
def test_unit_registry():
    """Test tripper.units.UnitRegistry."""
    from tripper.units import UnitRegistry

    ureg = UnitRegistry()
    u = ureg.Metre
    assert str(u) == "Metre"
    assert u.emmoIRI == "https://w3id.org/emmo#Metre"
    assert u.qudtIRI == "http://qudt.org/vocab/unit/M"

    q = ureg.Quantity("3 h")
    assert q.u.emmoIRI == "https://w3id.org/emmo#Hour"
    assert q.u.qudtIRI == "http://qudt.org/vocab/unit/HR"

    q = ureg.get_unit(iri="http://qudt.org/vocab/unit/PA")
    assert str(q) == "1 Pascal"

    info = ureg.get_unit_info(unitCode="DAY")
    assert info.name == "Day"
    assert info.emmoIRI == "https://w3id.org/emmo#Day"
