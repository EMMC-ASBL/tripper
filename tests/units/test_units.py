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


def emmo_quantity_value():
    """Test emmo_quantity_value()."""
    from tripper import EMMO, OWL, RDF, RDFS, Literal, Triplestore
    from tripper.units.units import emmo_quantity_value

    ts = Triplestore(backend="rdflib")
    EX = ts.bind("ex", "http://example.com/")
    ts.add_triples(
        [
            (EX.Width, RDF.type, OWL.Class),
            (EX.Width, RDFS.subClassOf, EMMO.Length),
            (EX.Width, RDFS.subClassOf, "_:r"),
            ("_:r", RDF.type, OWL.Restriction),
            ("_:r", OWL.onProperty, EMMO.hasSIQuantityValue),
            (
                "_:r",
                OWL.hasValue,
                Literal("2 mm", datatype=EMMO.SIQuantityDatatype),
            ),
            (EX.width, RDF.type, EMMO.Length),
            (
                EX.width,
                EMMO.hasSIQuantityValue,
                Literal("3 cm", datatype=EMMO.SIQuantityDatatype),
            ),
            (EX.BodyEnergy, RDF.type, OWL.Class),
            (EX.BodyEnergy, RDFS.subClassOf, EMMO.Energy),
            (EX.BodyEnergy, RDFS.subClassOf, "_:r2"),
            ("_:r2", RDF.type, OWL.Restriction),
            ("_:r2", OWL.onProperty, EMMO.hasNumericalPart),
            ("_:r2", OWL.hasValue, "_:v"),
            ("_:v", EMMO.hasNumberValue, Literal(1.1)),
            (EX.BodyEnergy, RDFS.subClassOf, "_:r3"),
            ("_:r3", RDF.type, OWL.Restriction),
            ("_:r3", OWL.onProperty, EMMO.hasReferencePart),
            ("_:r3", OWL.someValuesFrom, EMMO.MilliJoule),
            (EX.body_energy, RDF.type, EX.BodyEnergy),
            (EX.body_energy, EMMO.hasNumericalPart, EX.val),
            (EX.val, EMMO.hasNumberValue, Literal(2.2)),
            (EX.body_energy, EMMO.hasReferencePart, EMMO.Joule),
        ]
    )
    assert emmo_quantity_value(ts, EX.Width) == (2, "mm")
    assert emmo_quantity_value(ts, EX.width) == (3, "cm")
    assert emmo_quantity_value(ts, EX.BodyEnergy) == (1.1, EMMO.MilliJoule)
    assert emmo_quantity_value(ts, EX.body_energy) == (2.2, EMMO.Joule)


def test_units():
    """Test the Units class."""
    # pylint: disable=too-many-statements,protected-access

    from pathlib import Path

    from tripper import EMMO
    from tripper.units import Units
    from tripper.units.units import Dimension

    units = Units()

    # Test _emmo_units_iris()
    iris = units._emmo_unit_iris()
    assert len(iris) > 100
    assert EMMO.Ampere in iris
    assert EMMO.MilliMetre not in iris
    iris2 = units._emmo_unit_iris(include_prefixed=True)
    assert len(iris2) > len(iris)
    assert EMMO.MilliMetre in iris2

    # Test _emmo_quantity_iris()
    qiris = units._emmo_quantity_iris()
    assert len(qiris) > 100
    assert EMMO.Energy in qiris

    qiris2 = units._emmo_quantity_iris(constants=True)
    assert len(qiris2) > 10
    assert EMMO.PlanckConstant in qiris2

    # Test _get_unit_symbols()
    assert "Pa" in units._get_unit_symbols(EMMO.Pascal)
    assert "V" in units._get_unit_symbols(EMMO.Volt)
    assert "m²" in units._get_unit_symbols(EMMO.SquareMetre)

    # Test _get_unit_dimension_string()
    assert (
        units._get_unit_dimension_string(EMMO.UnitOne)
        == "T0 L0 M0 I0 Θ0 N0 J0"
    )
    assert (
        units._get_unit_dimension_string(EMMO.Joule)
        == "T-2 L+2 M+1 I0 Θ0 N0 J0"
    )
    assert (
        units._get_unit_dimension_string(EMMO.BecquerelPerCubicMetre)
        == "T-1 L-3 M0 I0 Θ0 N0 J0"
    )

    # Test _get_quantity_dimension_string()
    assert (
        units._get_quantity_dimension_string(EMMO.Length)
        == "T0 L+1 M0 I0 Θ0 N0 J0"
    )
    assert (
        units._get_quantity_dimension_string(EMMO.Energy)
        == "T-2 L+2 M+1 I0 Θ0 N0 J0"
    )
    assert (
        units._get_quantity_dimension_string(EMMO.FineStructureConstant)
        == "T0 L0 M0 I0 Θ0 N0 J0"
    )

    # Test _parse_dimension_string()
    assert units._parse_dimension_string(
        "T-2 L+2 M+1 I0 Θ0 N0 J0"
    ) == Dimension(-2, 2, 1, 0, 0, 0, 0)
    assert units._parse_dimension_string(
        "T0 L+1 M+1 I0 H-1 N+1 J0"
    ) == Dimension(0, 1, 1, 0, -1, 1, 0)

    # Test _parse_unitname()
    assert units._parse_unitname("Second") == (1, {"Second": 1})
    assert units._parse_unitname("GramPerSquareSecond") == (
        1,
        {"Second": -2, "Gram": 1},
    )
    assert units._parse_unitname("MolePerSquareMilliMetre") == (
        1e6,
        {"Metre": -2, "Mole": 1},
    )
    assert units._parse_unitname("PascalPerMilliLitre") == (
        1e3,
        {"Pascal": 1, "Litre": -1},
    )

    # Test _parse_units()
    # Skip, since it is slow and already used to initiate the units object.

    # Test _parse_quantities()
    # Skip, since it is slow and already used to initiate the units object.

    # Test get_unit()
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

    # Test write_pint_units()
    testdir = Path(__file__).resolve().parent.parent
    outdir = testdir / "output"
    units.write_pint_units(outdir / "units-emmo.txt")


# if True:
@pytest.mark.skipif(sys.version_info < (3, 9), reason="requires Python 3.9")
def test_unit_registry():
    """Test tripper.units.UnitRegistry."""
    from tripper import EMMO, RDFS, Triplestore
    from tripper.units import UnitRegistry
    from tripper.units.units import Dimension, MissingUnitError
    from tripper.utils import en

    ureg = UnitRegistry()

    # Test atteibute access
    u = ureg.Metre
    assert ureg["Metre"].u == u
    assert str(u) == "Metre"
    assert u.emmoIRI == "https://w3id.org/emmo#Metre"
    assert u.qudtIRI == "http://qudt.org/vocab/unit/M"
    assert u.info.name == "Metre"
    assert u.info.aliases == ["Meter"]

    # Test Quantity()
    q = ureg.Quantity("3 h")  # Hour exists in the ontology
    assert q.u.emmoIRI == "https://w3id.org/emmo#Hour"
    assert q.u.qudtIRI == "http://qudt.org/vocab/unit/HR"
    assert q.get_dimension() == q.u.info.dimension
    assert q.to_ontology_unit() == 3 * ureg.Hour

    q = ureg.Quantity("3 kh")  # KiloHour does NOT exists in the ontology
    with pytest.raises(MissingUnitError):
        q.u.info  # pylint: disable=pointless-statement
    assert q.get_dimension() == Dimension(1, 0, 0, 0, 0, 0, 0)
    assert q.to_ontology_unit() == 3000 * ureg.Hour

    q = ureg.Quantity("2 hJ")
    assert q.get_dimension() == Dimension(-2, 2, 1, 0, 0, 0, 0)
    assert q.to_ontology_unit() == 200 * ureg.Joule

    # Test get_unit()
    q = ureg.get_unit(iri="http://qudt.org/vocab/unit/PA")
    assert str(q) == "1 Pascal"

    # Test get_unit_info()
    info = ureg.get_unit_info(unitCode="DAY")
    assert info.name == "Day"
    assert info.emmoIRI == "https://w3id.org/emmo#Day"

    # Test save_quantity()
    ts = Triplestore(backend="rdflib")
    NS = ts.bind("", "http://example.com/test#")
    ts.bind("emmo", "https://w3id.org/emmo#")
    ureg.save_quantity(
        ts,
        ureg.Quantity(1.1, "Pa"),
        NS.ExperimentPressure,
        type=EMMO.Pressure,
        tbox=True,
        use_si_value=True,
        annotations={RDFS.label: en("ExperimentPressure")},
    )

    ureg.save_quantity(
        ts,
        ureg.Quantity(2.2, "°C"),
        NS.ExperimentTemperature,
        type=EMMO.ThermodynamicTemperature,
        tbox=True,
        use_si_value=False,
        annotations={RDFS.label: en("ExperimentTemperature")},
    )

    ureg.save_quantity(
        ts,
        ureg.Quantity(3.3, "J"),
        NS.ExperimentEnergy,
        type=EMMO.Energy,
        tbox=False,
        use_si_value=True,
        annotations={RDFS.label: en("ExperimentEnergy")},
    )

    ureg.save_quantity(
        ts,
        ureg.Quantity(4.4, "km/h"),
        NS.ExperimentSpeed,
        type=EMMO.Speed,
        tbox=False,
        use_si_value=False,
        annotations={RDFS.label: en("ExperimentSpeed")},
    )

    print(ts.serialize())

    # Test load_quantity()
    pressure = ureg.load_quantity(ts, NS.ExperimentPressure)
    assert abs((pressure - ureg.Quantity(1.1, "Pa")).m) < 1e-7

    temp = ureg.load_quantity(ts, NS.ExperimentTemperature)
    assert abs((temp - ureg.Quantity(2.2, "°C")).m) < 1e-7

    energy = ureg.load_quantity(ts, NS.ExperimentEnergy)
    assert abs((energy - ureg.Quantity(3.3, "J")).m) < 1e-7

    speed = ureg.load_quantity(ts, NS.ExperimentSpeed)
    assert abs((speed - ureg.Quantity(4.4, "km/h")).m) < 1e-7
