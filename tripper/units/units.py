"""A module for handling units using EMMO as the main resource.

Pint is used for programatic unit conversions.
"""

import pickle  # nosec
import re
import warnings
from collections import namedtuple
from typing import TYPE_CHECKING

import pint

from tripper import EMMO, RDFS, SKOS, Namespace, Triplestore
from tripper.errors import TripperError
from tripper.namespace import get_cachedir
from tripper.utils import AttrDict

if TYPE_CHECKING:  # pragma: no cover
    from pathlib import Path
    from typing import Any, Iterable, Mapping, Optional, Union

    # from pint.compat import TypeAlias

# Default EMMO version
EMMO_VERSION = "1.0.0"

# Cached module variables
_emmo_ts = None  # EMMO triplestore object
_emmo_ns = None  # EMMO namespace object
_unit_cache: dict = {}  # Maps unit names to IRIs

# Named tuple used to represent a dimension string
# Note we use H instead of ϴ to represent the thermodynamic temperature
Dimension = namedtuple("Dimension", "T,L,M,I,H,N,J")
Dimension.__doc__ = "SI quantity dimension"
Dimension.T.__doc__ = "time"
Dimension.L.__doc__ = "length"
Dimension.M.__doc__ = "mass"
Dimension.I.__doc__ = "electric current"
Dimension.H.__doc__ = "thermodynamic temperature"
Dimension.N.__doc__ = "amount of substance"
Dimension.J.__doc__ = "luminous intensity"


class UnitError(TripperError):
    """Base Error for units module."""


class MissingUnitError(UnitError):
    """Unit not found in ontology."""


class MissingDimensionStringError(UnitError):
    """Unit does not have a dimensional string."""


class InvalidDimensionStringError(UnitError):
    """Invalid dimension string."""


class PermissionWarning(UserWarning):
    """Not enough permissions."""


def get_emmo_triplestore(emmo_version: str = EMMO_VERSION) -> Triplestore:
    """Return, potentially cached, triplestore object containing the
    given version of EMMO."""
    global _emmo_ts  # pylint: disable=global-statement
    if not _emmo_ts:
        _emmo_ts = Triplestore("rdflib")

        cachefile = get_cachedir() / f"emmo-{emmo_version}.ntriples"
        if cachefile.exists():
            _emmo_ts.parse(cachefile, format="ntriples")
        else:
            _emmo_ts.parse(f"https://w3id.org/emmo/{emmo_version}")
            try:
                _emmo_ts.serialize(
                    cachefile, format="ntriples", encoding="utf-8"
                )
            except PermissionError as exc:
                warnings.warn(
                    f"{exc}: {cachefile}",
                    category=PermissionWarning,
                )
    return _emmo_ts


def get_emmo_namespace(emmo_version: str = EMMO_VERSION) -> Namespace:
    """Return potentially cached EMMO namespace object."""
    global _emmo_ns  # pylint: disable=global-statement
    if not _emmo_ns:
        _emmo_ns = Namespace(
            iri="https://w3id.org/emmo#",
            label_annotations=True,
            check=True,
            triplestore=get_emmo_triplestore(emmo_version),
        )
    return _emmo_ns


def base_unit_expression(dimension: Dimension) -> str:
    """Return a base unit expression corresponding to `dimension`."""
    base_units = (
        "Second",
        "Metre",
        "Kilogram",
        "Ampere",
        "Kelvin",
        "Mole",
        "Candela",
    )
    expr = []
    for b, e in zip(base_units, dimension):
        if e:
            power = "" if e == 1 else f"**{e}"
            expr.append(f"{b}{power}")
    return " * ".join(expr) if expr else "1"


class Units:
    """A class representing all units in an EMMO-based ontology."""

    def __init__(
        self,
        ts: "Optional[Triplestore]" = None,
        unit_ontology: str = "emmo",
        ontology_version: str = EMMO_VERSION,
        include_prefixed: bool = False,
        cache: "Optional[bool]" = True,
    ) -> None:
        """Initialise a Units class from triplestore `ts`

        Arguments:
            ts: Triplestore object containing the ontology to load
                units from.  The default is to determine the ontology to
                load from `unit_ontology` and `ontology_version`.
            unit_ontology: Name of unit ontology to parse. Currently only
                "emmo" is supported.
            ontology_version: Version of `unit_ontology` to load if `ts` is
                None.
            include_prefixed: Whether to also include prefixed units.
            cache: Whether to cache the unit table. If `cache` is:
                - True: Load cache if it exists, otherwise create new cache.
                - False: Don't use cache.
                - None: Don't load cache, but (over)write new cache.

        """
        if ts:
            self.ts = ts
        elif unit_ontology == "emmo":
            self.ts = get_emmo_triplestore(ontology_version)
        else:
            raise ValueError(f"Unsupported unit ontology: {unit_ontology}")

        self.ns = Namespace(
            iri="https://w3id.org/emmo#",
            label_annotations=True,
            check=True,
            triplestore=self.ts,
        )

        pf = "-prefixed" if include_prefixed else ""
        fname = f"units-{unit_ontology}-{ontology_version}{pf}.pickle"
        cachedir = get_cachedir()
        cachefile = cachedir / fname
        if cache and cachefile.exists():
            with open(cachefile, "rb") as f:
                self.units = pickle.load(f)  # nosec
        else:
            self.units = self._parse_units(include_prefixed=include_prefixed)

        if cache in (True, None):
            try:
                cachedir.mkdir(parents=True, exist_ok=True)
            except PermissionError as exc:
                warnings.warn(
                    f"{exc}: {cachedir}",
                    category=PermissionWarning,
                )
            else:
                with open(cachefile, "wb") as f:
                    pickle.dump(self.units, f)

        self.unit_ontology = unit_ontology
        self.ontology_version = ontology_version
        self.cachefile = cachefile

    def _emmo_unit_iris(self, include_prefixed: bool = False) -> list:
        """Return a list with the IRIs of all EMMO units.

        If `include_prefixed` is true, also return prefixed units.
        """
        prefixfilter = (
            ""
            if include_prefixed
            else (
                "FILTER NOT EXISTS "
                f"{{ ?unit rdfs:subClassOf <{EMMO.PrefixedUnit}> . }}"
            )
        )
        query = f"""
        PREFIX rdfs: <{RDFS}>
        SELECT ?unit
        WHERE {{
          ?unit rdfs:subClassOf+ ?dimunit .
          ?dimunit rdfs:subClassOf ?r .
          ?r owl:onProperty <{EMMO.hasDimensionString}> .
          {prefixfilter}
        }}
        """
        # Bug in mupy... seems to be fixed in master
        return [iri for iri, in self.ts.query(query)]  # type: ignore

    def _get_unit_symbols(self, iri: str) -> list:
        """Return a list with unit symbols for unit with the given IRI."""
        symbols = []
        for r in self.ts.restrictions(
            iri, self.ns.unitSymbolValue, type="value"
        ):
            symbols.append(str(r["value"]))

        for symbol in self.ts.value(iri, self.ns.unitSymbol, any=None):
            s = str(symbol)
            symbols.append(f"1{s}" if s.startswith("/") else s)

        return symbols

    def _get_dimension_string(self, iri: str) -> str:
        """Return the dimension string for unit with the given IRI."""
        query = f"""
        PREFIX rdfs: <{RDFS}>
        SELECT ?dimstr
        WHERE {{
          <{iri}> rdfs:subClassOf+ ?r .
          ?r owl:onProperty <{EMMO.hasDimensionString}> .
          ?r owl:hasValue ?dimstr .
        }}
        """
        result = self.ts.query(query)
        if result:
            # Bug in mupy
            return result[0][0]  # type: ignore
        raise MissingDimensionStringError(iri)

    def _parse_dimension_string(self, dimstr: str) -> "Any":
        # TODO: replace return type with namedtuple when that is supported
        # by mupy
        """Parse dimension string and return it as a named tuple."""
        m = re.match(
            "^T([+-][1-9][0-9]*|0) L([+-][1-9][0-9]*|0) M([+-][1-9][0-9]*|0) "
            "I([+-][1-9][0-9]*|0) [ΘϴH]([+-][1-9][0-9]*|0) "
            "N([+-][1-9][0-9]*|0) J([+-][1-9][0-9]*|0)$",
            dimstr,
        )
        if m:
            return Dimension(*[int(d) for d in m.groups()])
        raise InvalidDimensionStringError(dimstr)

    def _parse_units(self, include_prefixed=False) -> "dict[str, AttrDict]":
        """Parse EMMO units and return them as an iterator over named
        tuples.

        Arguments:
            include_prefixed: Whether to return prefixed units.
        """
        d = {}
        for iri in self._emmo_unit_iris(include_prefixed=include_prefixed):
            name = str(self.ts.value(iri, SKOS.prefLabel))
            dimstr = str(self._get_dimension_string(iri))
            dimension = self._parse_dimension_string(dimstr)
            mult = list(
                self.ts.restrictions(
                    iri, property=EMMO.hasSIConversionMultiplier
                )
            )
            offset = list(
                self.ts.restrictions(iri, property=EMMO.hasSIConversionOffset)
            )
            qudtIRI = self.ts.value(iri, EMMO.qudtReference, any=True)
            omIRI = self.ts.value(iri, EMMO.omReference, any=True)

            d[name] = AttrDict(
                name=name,
                description=self.ts.value(iri, EMMO.elucidation),
                aliases=[
                    str(s) for s in self.ts.value(iri, SKOS.altLabel, any=None)
                ],
                symbols=self._get_unit_symbols(iri),
                dimension=dimension,
                emmoIRI=iri,
                qudtIRI=str(qudtIRI) if qudtIRI else None,
                omIRI=str(omIRI) if omIRI else None,
                ucumCodes=[
                    str(s) for s in self.ts.value(iri, EMMO.ucumCode, any=None)
                ],
                unitCode=str(self.ts.value(iri, EMMO.uneceCommonCode)),
                multiplier=float(mult[0]["value"]) if mult else None,
                offset=float(offset[0]["value"]) if offset else None,
            )
        return d

    def get_unit(
        self,
        name: "Optional[str]" = None,
        symbol: "Optional[str]" = None,
        iri: "Optional[str]" = None,
        unitCode: "Optional[str]" = None,
    ) -> AttrDict:
        """Find unit by one of the arguments and return a dict describing it.

        Argument:
            name: Search for unit by name. Ex: "Ampere"
            symbol: Search for unit by symbol or UCUM code. Ex: "A", "km"
            iri: Search for unit by IRI.
            unitCode: Search for unit by UNECE common code. Ex: "MTS"

        Returns:
            A dict with attribute access describing the unit. The dict has
            the following keys:

              - name: Preferred label.
              - description: Unit description.
              - aliases: List of alternative labels.
              - symbols: List with unit symbols.
              - dimension: Named tuple with quantity dimension.
              - emmoIRI: IRI of the unit in the EMMO ontology.
              - qudtIRI: IRI of the unit in the QUDT ontology.
              - omIRI: IRI of the unit in the OM ontology.
              - ucumCodes: List of UCUM codes for the unit.
              - unitCode: UNECE common code for the unit.
              - multiplier: Unit multiplier.
              - offset: Unit offset.
        """
        if name and name in self.units:
            return self.units[name]

        for unit in self.units.values():
            if name and name in unit.aliases:
                return unit
            if symbol and (symbol in unit.symbols or symbol in unit.ucumCodes):
                return unit
            if iri and iri in (unit.emmoIRI, unit.qudtIRI, unit.omIRI):
                return unit
            if unitCode and unitCode == unit.unitCode:
                return unit

        # As a fallback, try case insensitive search for labels
        if name:
            lowername = name.lower()
            for unit in self.units.values():
                if lowername == unit.name.lower() or lowername in set(
                    s.lower() for s in unit.aliases
                ):
                    return unit

        msg = (
            f"name={name}"
            if name
            else (
                f"symbol={symbol}"
                if symbol
                else (
                    f"iri={iri}"
                    if iri
                    else (
                        f"unitCode={unitCode}"
                        if unitCode
                        else "missing search argument"
                    )
                )
            )
        )
        raise MissingUnitError(msg)

    def write_pint_units(self, filename: "Union[str, Path]") -> None:
        """Write Pint units definition to `filename`."""
        # pylint: disable=too-many-branches

        # For now, include prefixes and base units...
        content: list = [
            "# Pint units definitions file",
            (
                "# Created with tripper.units from "
                f"{self.unit_ontology}-{self.ontology_version}"
            ),
            "",
            "# Decimal prefixes",
            "quecto- = 1e-30 = q-",
            "ronto- = 1e-27 = r-",
            "yocto- = 1e-24 = y-",
            "zepto- = 1e-21 = z-",
            "atto- =  1e-18 = a-",
            "femto- = 1e-15 = f-",
            "pico- =  1e-12 = p-",
            "nano- =  1e-9  = n-",
            "micro- = 1e-6  = µ- = μ- = u-",
            "milli- = 1e-3  = m-",
            "centi- = 1e-2  = c-",
            "deci- =  1e-1  = d-",
            "deca- =  1e+1  = da- = deka-",
            "hecto- = 1e2   = h-",
            "kilo- =  1e3   = k-",
            "mega- =  1e6   = M-",
            "giga- =  1e9   = G-",
            "tera- =  1e12  = T-",
            "peta- =  1e15  = P-",
            "exa- =   1e18  = E-",
            "zetta- = 1e21  = Z-",
            "yotta- = 1e24  = Y-",
            "ronna- = 1e27  = R-",
            "quetta- = 1e30 = Q-",
            "",
            "# Binary prefixes",
            "kibi- = 2**10 = Ki-",
            "mebi- = 2**20 = Mi-",
            "gibi- = 2**30 = Gi-",
            "tebi- = 2**40 = Ti-",
            "pebi- = 2**50 = Pi-",
            "exbi- = 2**60 = Ei-",
            "zebi- = 2**70 = Zi-",
            "yobi- = 2**80 = Yi-",
            "",
            "# Base units",
            "Second = [time] = s = second",
            "Metre = [length] = m = metre = meter",
            # Note: gram is used instead of kilogram to get prefixes right...
            "Gram = [mass] = g = gram",
            "Ampere = [current] = A = ampere",
            "Kelvin = [temperature]; offset: 0 = K = kelvin",
            "Mole = [substance] = mole = mol",
            "Candela = [luminosity] = cd = candela",
            "",
            "# Units",
        ]

        snake_pattern = re.compile(r"(?<!^)(?=[A-Z])")

        skipunits = {
            "Second",
            "Metre",
            "Gram",
            "Kilogram",
            "Ampere",
            "Kelvin",
            "Mole",
            "Candela",
        }
        for unit in self.units.values():
            if unit.name in skipunits:
                continue

            baseexpr = base_unit_expression(unit.dimension)
            mult = f"{unit.multiplier} * " if unit.multiplier != 1.0 else ""
            if unit.multiplier or unit.offset:
                if unit.multiplier and unit.offset:
                    s = [
                        f"{unit.name} = {mult}{baseexpr}; "
                        f"offset: {unit.offset}"
                    ]
                elif unit.multiplier:
                    s = [f"{unit.name} = {mult}{baseexpr}"]
                elif unit.offset:
                    s = [f"{unit.name} = {baseexpr}; offset: {unit.offset}"]
                else:
                    assert False, "should never happen"  # nosec
            elif baseexpr == "1":
                s = [f"{unit.name} = []"]
            else:
                s = [f"{unit.name} = {baseexpr}"]

            # table = str.maketrans({x: None for x in " .⋅·/*{}"})
            table = str.maketrans({x: None for x in " ./*{}"})
            symbols = [s for s in unit.symbols if s.translate(table) == s]
            if symbols:
                s.extend(f" = {symbol}" for symbol in symbols)
            else:
                s.append(" = _")

            snake = snake_pattern.sub("_", unit.name).lower()
            if snake != unit.name:
                s.append(f" = {snake}")

            for alias in unit.aliases:
                if " " not in alias:
                    s.append(f" = {alias}")

            content.append(" ".join(s))

        with open(filename, "wt", encoding="utf-8") as f:
            f.write("\n".join(content) + "\n")

    def clear_cache(self):
        """Clear caches used by this Units object."""
        cachefile = self.cachefile
        if cachefile.exists():
            cachefile.unlink()

        cachedir = cachefile.parent
        fname = f"{self.unit_ontology}-{self.ontology_version}.ntriples"
        ontofile = cachedir / fname
        if ontofile.exists():
            ontofile.unlink()


# pylint: disable=too-many-ancestors
class Unit(pint.Unit):
    """A subclass of pint.Unit with additional methods and properties."""

    def get_unit_info(self):
        """Return a dict with attribute access describing the unit.

        SeeAlso:
            tripper.units.UnitRegistry.get_unit_info()
        """
        ureg = self._REGISTRY
        return ureg.get_unit_info(str(self))

    emmoIRI = property(
        lambda self: self.get_unit_info().emmoIRI,
        doc="IRI of the unit in the EMMO ontology.",
    )
    qudtIRI = property(
        lambda self: self.get_unit_info().qudtIRI,
        doc="IRI of the unit in the QUDT ontology.",
    )
    omIRI = property(
        lambda self: self.get_unit_info().omIRI,
        doc="IRI of the unit in the OM ontology.",
    )


class Quantity(pint.Quantity):
    """A subclass of pint.Quantity with support for tripper.units."""


class UnitRegistry(pint.UnitRegistry):
    """A subclass of pint.UnitRegistry with support for loading units
    from ontologies.
    """

    Unit: "Any" = Unit
    Quantity: "Any" = Quantity

    def __init__(
        self,
        *args: "Any",
        ts: "Optional[Triplestore]" = None,
        unit_ontology: str = "emmo",
        ontology_version: str = EMMO_VERSION,
        include_prefixed: bool = False,
        cache: "Optional[bool]" = True,
        **kwargs: "Any",
    ) -> None:
        """Initialise a Units class from triplestore `ts`

        Arguments:
            args: Positional arguments passed to pint.UnitRegistry().
            ts: Triplestore object containing the ontology to load
                units from.  The default is to determine the ontology to
                load from `unit_ontology` and `ontology_version`.
            unit_ontology: Name of unit ontology to parse. Currently only
                "emmo" is supported.
            ontology_version: Version of `unit_ontology` to load if `ts` is
                None.
            include_prefixed: Whether to also include prefixed units.
            cache: Whether to cache the unit table. If `cache` is:
                - True: Load cache if it exists, otherwise create new cache.
                - False: Don't use cache.
                - None: Don't load cache, but (over)write new cache.
            kwargs: Keyword arguments passed to pint.UnitRegistry().

        Examples:
            >>> from tripper.units import UnitRegistry
            >>> ureg = UnitRegistry()
            >>> u = ureg.Metre
            >>> u
            <Unit('Metre')>

            >>> u.emmoIRI  # doctest: +SKIP
            'https://w3id.org/emmo#Metre'

            >>> q = ureg.Quantity("3 h")
            >>> q
            <Quantity(3, 'Hour')>

            >>> q.u.qudtIRI  # doctest: +SKIP
            'http://qudt.org/vocab/unit/HR'

        """
        self._tripper_cachedir = get_cachedir()
        self._tripper_units: "Optional[Units]" = None
        self._tripper_unitsargs = (
            ts,
            unit_ontology,
            ontology_version,
            include_prefixed,
            cache,
        )

        # If no explicit `filename` is not provided, ensure that an unit
        # definition file has been created and assign `filename` to it.
        fname = f"units-{unit_ontology}-{ontology_version}.txt"
        unitsfile = self._tripper_cachedir / fname
        if "filename" not in kwargs:
            kwargs["filename"] = unitsfile
            if not unitsfile.exists():
                units = self._get_tripper_units()
                self._tripper_cachedir.mkdir(parents=True, exist_ok=True)
                units.write_pint_units(unitsfile)

        super().__init__(*args, **kwargs)
        self._tripper_unitsfile = unitsfile

    def _get_tripper_units(self) -> Units:
        """Returns a tripper.units.Units instance for the current ontology."""
        if not self._tripper_units:
            self._tripper_units = Units(*self._tripper_unitsargs)
        return self._tripper_units

    def get_unit(
        self,
        name: "Optional[str]" = None,
        symbol: "Optional[str]" = None,
        iri: "Optional[str]" = None,
        unitCode: "Optional[str]" = None,
    ) -> "Any":
        """Return unit matching any of the arguments.

        Argument:
            name: Search for unit by name. Ex: "Ampere"
            symbol: Search for unit by symbol or UCUM code. Ex: "A", "km"
            iri: Search for unit by IRI.
            unitCode: Search for unit by UNECE common code. Ex: "MTS"

        Returns:
            Return matching unit.
        """
        info = self.get_unit_info(
            name=name, symbol=symbol, iri=iri, unitCode=unitCode
        )
        return self[info.name]

    def get_unit_info(
        self,
        name: "Optional[str]" = None,
        symbol: "Optional[str]" = None,
        iri: "Optional[str]" = None,
        unitCode: "Optional[str]" = None,
    ) -> AttrDict:
        """Return information about a unit.

        Argument:
            name: Search for unit by name. Ex: "Ampere"
            symbol: Search for unit by symbol or UCUM code. Ex: "A", "km"
            iri: Search for unit by IRI.
            unitCode: Search for unit by UNECE common code. Ex: "MTS"

        Returns:
            A dict with attribute access describing the unit. The dict has
            the following keys:

              - name: Preferred label.
              - description: Unit description.
              - aliases: List of alternative labels.
              - symbols: List with unit symbols.
              - dimension: Named tuple with quantity dimension.
              - emmoIRI: IRI of the unit in the EMMO ontology.
              - qudtIRI: IRI of the unit in the QUDT ontology.
              - omIRI: IRI of the unit in the OM ontology.
              - ucumCodes: List of UCUM codes for the unit.
              - unitCode: UNECE common code for the unit.
              - multiplier: Unit multiplier.
              - offset: Unit offset.

        """
        units = self._get_tripper_units()
        return units.get_unit(
            name=name, symbol=symbol, iri=iri, unitCode=unitCode
        )

    def clear_cache(self):
        """Clear caches related to this unit registry."""
        if self._tripper_unitsfile.exists():
            self._tripper_unitsfile.unlink()

        ontology, version = self._tripper_unitsargs[1:3]
        cachedir = self._tripper_cachedir
        ontofile = cachedir / f"{ontology}-{version}.ntriples"
        unitsfile = cachedir / f"units-{ontology}-{version}.pickle"
        if ontofile.exists():
            ontofile.unlink()
        if unitsfile.exists():
            unitsfile.unlink()
