"""A module for handling units using EMMO as the main resource.

Pint is used for programatic unit conversions.
"""

# pylint: disable=too-few-public-methods,too-many-lines

import math
import pickle  # nosec
import re
import warnings
from collections import namedtuple
from typing import TYPE_CHECKING
from urllib.parse import urlparse

import pint

from tripper import (
    EMMO,
    OWL,
    RDF,
    RDFS,
    SCHEMA,
    SKOS,
    Literal,
    Namespace,
    Triplestore,
)
from tripper.errors import IRIExistsError, PermissionWarning, TripperError
from tripper.namespace import get_cachedir
from tripper.utils import AttrDict, bnode_iri

if TYPE_CHECKING:  # pragma: no cover
    from pathlib import Path, PurePath
    from typing import Any, Iterable, Mapping, Optional, Tuple, Union

    from pint.compat import TypeAlias


# Default EMMO version
EMMO_VERSION = "1.0.0"

# Cached module variables
_unit_ts = None  # Unit triplestore object
_unit_reg = None  # Default unit registry

# Named tuple used to represent a dimension string
# Note we use H instead of ϴ to represent the thermodynamic temperature
Dimension = namedtuple("Dimension", "T,L,M,I,H,N,J")
Dimension.__doc__ = "SI quantity dimension"
Dimension.T.__doc__ = "Time"
Dimension.L.__doc__ = "Length"
Dimension.M.__doc__ = "Mass"
Dimension.I.__doc__ = "ElectricCurrent"
Dimension.H.__doc__ = "ThermodynamicTemperature"
Dimension.N.__doc__ = "AmountOfSubstance"
Dimension.J.__doc__ = "LuminousIntensity"


class UnitError(TripperError):
    """Base Error for units module."""


class MissingUnitError(UnitError):
    """Unit not found in ontology."""


class MissingDimensionStringError(UnitError):
    """Unit does not have a dimensional string."""


class InvalidDimensionStringError(UnitError):
    """Invalid dimension string."""


class NoDefaultUnitRegistryError(UnitError):
    """No default unit registry has been defined."""


def get_ureg(*args, nocreate=False, **kwargs) -> "UnitRegistry":
    """Return default unit registry.

    If a default unit registry has been set (using the
    `UnitRegistry.set_as_default()` method), it is returned.

    If no default unit registry has been set and `nocreate` is true,
    a `NoDefaultUnitRegistryError` exception is raised. Otherwise,
    a new default unit registry is created using the `args` and `kwargs`
    arguments.

    """
    global _unit_reg  # pylint: disable=global-statement
    if not _unit_reg:
        if nocreate:
            raise NoDefaultUnitRegistryError("No default unit registry")
        ureg = UnitRegistry(*args, **kwargs)
        _unit_reg = ureg
    else:
        ureg = _unit_reg
    return ureg


def _default_url_name(url, name) -> tuple:
    "Return default unit triplestore url and name."
    if url is None:
        url = f"https://w3id.org/emmo/{EMMO_VERSION}"
        if not name:
            name = f"emmo-{EMMO_VERSION}"
    elif not name:
        raise ValueError("`name` must be given with `url`")
    return url, name


def get_unit_triplestore(
    url: "Optional[Union[str, Path]]" = None,
    format: "Optional[str]" = None,  # pylint: disable=redefined-builtin
    name: "Optional[str]" = None,
    cache: "Union[bool, None]" = True,
) -> Triplestore:
    """Return, potentially cached, triplestore object that defines the units.

    Arguments:
        url: URL or path to unit triplestore.
            Default: "https://w3id.org/emmo/{EMMO_VERSION}"
        format: Optional format of the source referred to by `url`.
        name: A (versioned) name for the triplestore. Used for caching.
            Ex: "emmo-1.0.0".
        cache: Whether to load from cache. If `cache` is:
            - True: Load cache if it exists, otherwise create new cache.
            - False: Don't load cache, but (over)write new cache.
            - None: Don't use cache.

    """
    global _unit_ts  # pylint: disable=global-statement
    if not _unit_ts:
        _unit_ts = Triplestore("rdflib")
        url, name = _default_url_name(url, name)

        cachefile = get_cachedir() / f"units-{name}.ntriples"
        if cache and cachefile.exists():
            _unit_ts.parse(cachefile, format="ntriples")
        else:
            print("* parsing units triplestore... ", end="", flush=True)
            _unit_ts.parse(url, format=format)
            print("done")
            if cache is not None:
                try:
                    _unit_ts.serialize(
                        cachefile, format="ntriples", encoding="utf-8"
                    )
                except PermissionError as exc:
                    warnings.warn(
                        f"{exc}: {cachefile}",
                        category=PermissionWarning,
                    )
    return _unit_ts


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


def load_emmo_quantity(ts: Triplestore, iri: str) -> "Tuple[float, str]":
    """Return value and unit for EMMO quantity with given `iri`."""
    isclass = ts.query(f"ASK {{<{iri}> a owl:Class}}")

    def value_restriction_query(prop, target="hasValue", number=False):
        """Return SPARQL query for value restriction for property `prop`."""
        crit1 = f"?r owl:{target} ?qvalue ."
        crit2 = f"?r owl:{target} ?v .\n  ?v <{EMMO.hasNumberValue}> ?qvalue ."
        crit = crit2 if number else crit1
        return f"""
        PREFIX rdfs: <{RDFS}>
        SELECT ?qvalue
        WHERE {{
          <{iri}> rdfs:subClassOf+ ?r .
          # ?r a owl:Restriction .
          ?r owl:onProperty <{prop}> .
          {crit}
        }}
        """

    # Check for emmo:hasSIQuantityValue
    if isclass:
        result = ts.query(value_restriction_query(EMMO.hasSIQuantityValue))
        qval = result[0][0] if result else None
    else:
        result = ts.value(iri, EMMO.hasSIQuantityValue)
        qval = str(result) if result else None

    if qval:
        m = re.match(
            r"([+-]?[0-9]*\.?[0-9]*([eE][+-]?[0-9]+)?)[ *⋅]*(.*)?", qval
        )
        if m:
            value, _, unit = m.groups()
            return float(value), unit

    # Check for emmo:hasNumericalPart/emmo:hasReferencePart
    if isclass:
        num = ts.query(
            value_restriction_query(EMMO.hasNumericalPart, number=True)
        )
        ref = ts.query(
            value_restriction_query(
                EMMO.hasReferencePart, target="someValuesFrom"
            )
        )[0][0]
    else:
        num = ts.query(
            f"""
        SELECT ?qvalue WHERE {{
          <{iri}> <{EMMO.hasNumericalPart}> ?v .
          ?v <{EMMO.hasNumberValue}> ?qvalue .
        }}
        """
        )
        ref = ts.value(iri, EMMO.hasReferencePart)

    return float(num[0][0]), ref


def save_emmo_quantity(
    ts: Triplestore,
    q: "Quantity",
    iri: str,
    type: "Optional[str]" = None,  # pylint: disable=redefined-builtin
    tbox: bool = False,
    si_datatype: bool = True,
    annotations: "Optional[dict]" = None,
) -> None:
    """Save quantity to triplestore.

    Arguments:
        ts: Triplestore to save to.
        q: Quantity to save.
        iri: IRI of the quantity in the triplestore.
        type: IRI of the type or superclass (if `tbox` is true) of the
            quantity.
        tbox: Whether to document the quantity in the tbox.
        si_datatype: Whether to represent the value using the
            `emmo:SIQuantityDatatype` datatype.
        annotations: Additional annotations describing the quantity.
            Use Literal() for literal annotations.

    """
    if EMMO not in ts.namespaces.values():
        ts.bind("emmo", EMMO)

    if ts.has(iri):
        raise IRIExistsError(iri)

    if not type:
        type = EMMO.Quantity

    triples = [(iri, RDF.type, OWL.Class if tbox else type)]
    if tbox:
        r = bnode_iri("restriction")
        triples.extend(
            [
                (iri, RDFS.subClassOf, type),
                (iri, RDFS.subClassOf, r),
                (r, RDF.type, OWL.Restriction),
            ]
        )
        if si_datatype:
            triples.extend(
                [
                    (r, OWL.onProperty, EMMO.hasSIQuantityValue),
                    (r, OWL.hasValue, Literal(q)),
                ]
            )
        else:
            v = bnode_iri("value")
            r2 = bnode_iri("restriction")
            q2 = q.to_ontology_units()
            triples.extend(
                [
                    (r, OWL.onProperty, EMMO.hasNumericalPart),
                    (r, OWL.hasValue, v),
                    (v, EMMO.hasNumberValue, Literal(q2.m)),
                    (iri, RDFS.subClassOf, r2),
                    (r2, RDF.type, OWL.Restriction),
                    (r2, OWL.onProperty, EMMO.hasReferencePart),
                    (r2, OWL.someValuesFrom, q2.u.emmoIRI),
                ]
            )
    else:
        if si_datatype:
            triples.append((iri, EMMO.hasSIQuantityValue, Literal(q)))
        else:
            v = bnode_iri("value")
            q2 = q.to_ontology_units()
            triples.extend(
                [
                    (iri, EMMO.hasNumericalPart, v),
                    (v, EMMO.hasNumberValue, Literal(q2.m)),
                    (iri, EMMO.hasReferencePart, q2.u.emmoIRI),
                ]
            )

    if annotations:
        for pred, obj in annotations.items():
            triples.append((iri, pred, obj))

    ts.add_triples(triples)


class Units:
    """A class representing all units in an EMMO-based ontology."""

    # pylint: disable=too-many-instance-attributes

    def __init__(
        self,
        ts: "Optional[Triplestore]" = None,
        url: "Optional[Union[str, Path]]" = None,
        format: "Optional[str]" = None,  # pylint: disable=redefined-builtin
        name: "Optional[str]" = None,
        formalisation: str = "emmo",
        include_prefixed: bool = False,
        cache: "Union[bool, None]" = True,
    ) -> None:
        """Initialise a Units class from triplestore `ts`

        Arguments:
            ts: Triplestore object containing the ontology to load
                units from.
            url: URL (or path) to triplestore from where to load the unit
                definitions if `ts` is not given.
                Default: "https://w3id.org/emmo/{EMMO_VERSION}"
            format: Optional format of the source referred to by `url`.
            name: A (versioned) name for the triplestore. Used for caching.
                Ex: "emmo-1.0.0".
            formalisation: The ontological formalisation with which units
                and quantities are represented. Currently only "emmo" is
                supported.
            include_prefixed: Whether to also include prefixed units.
            cache: Whether to cache the unit table. If `cache` is:
                - True: Load cache if it exists, otherwise create new cache.
                - False: Don't load cache, but (over)write new cache.
                - None: Don't use cache.

        """
        url, name = _default_url_name(url, name)

        if ts:
            self.ts = ts
        else:
            self.ts = get_unit_triplestore(
                url=url, format=format, name=name, cache=cache
            )

        self.ns = Namespace(
            iri="https://w3id.org/emmo#",
            label_annotations=True,
            check=True,
            triplestore=self.ts,
        )

        pf = "-prefixed" if include_prefixed else ""
        fname = f"units{pf}-{name}.pickle"
        cachedir = get_cachedir(create=True)
        cachefile = cachedir / fname
        if cache and cachefile.exists():
            with open(cachefile, "rb") as f:
                d = pickle.load(f)  # nosec
                self.units = d["units"]
                self.quantities = d["quantities"]
                self.constants = d["constants"]
        else:
            print("* parsing units... ", end="", flush=True)
            self.units = self._parse_units(include_prefixed=include_prefixed)
            print("done\n* parsing quantities... ", end="", flush=True)
            self.quantities = self._parse_quantities(constants=False)
            print("done\n* parsing constants... ", end="", flush=True)
            self.constants = self._parse_quantities(constants=True)
            print("done")

        if cache is not None:
            with open(cachefile, "wb") as f:
                d = {
                    "units": self.units,
                    "quantities": self.quantities,
                    "constants": self.constants,
                }
                pickle.dump(d, f)

        self.url = url
        self.name = name
        self.formalisation = formalisation
        self.cachedir = cachedir
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

    def _emmo_quantity_iris(self, constants: bool = False) -> list:
        """Return a list with the IRIs of all EMMO quantities.

        If `constants` is true, only physical constants are returned,
        otherwise all quantities, but physical constants are returned.
        """
        # Note, we liberately do not include
        #
        #    ?q rdfs:subClassOf+ <{EMMO.Quantity}> .
        #
        # in the query, since that makes it very slow.
        constonly = "" if constants else "NOT"
        query = f"""
        PREFIX rdfs: <{RDFS}>
        PREFIX owl: <{OWL}>
        SELECT ?q
        WHERE {{
          # {{
          #   SELECT ?q WHERE {{
          #     ?q rdfs:subClassOf+ <{EMMO.Quantity}> .
          #   }}
          # }}
          ?q rdfs:subClassOf* ?r .
          ?r owl:onProperty <{EMMO.hasMeasurementUnit}> .
          FILTER {constonly} EXISTS {{
            ?q rdfs:subClassOf+ <{EMMO.PhysicalConstant}> .
          }}
          FILTER (!isBlank(?q))
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

    def _get_unit_dimension_string(self, iri: str) -> str:
        """Return the dimension string for unit with the given IRI."""
        query = f"""
        PREFIX rdfs: <{RDFS}>
        PREFIX owl: <{OWL}>
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

    def _get_quantity_dimension_string(self, iri: str) -> str:
        """Return the dimension string for quantity with the given IRI."""
        # Note, the use of subquery greately speeds up this SPARQL query
        query = f"""
        PREFIX rdfs: <{RDFS}>
        PREFIX owl: <{OWL}>
        SELECT ?dimstr
        WHERE {{
          {{
            SELECT ?dimunit WHERE {{
              <{iri}> rdfs:subClassOf+ ?r .
              ?r owl:onProperty <{EMMO.hasMeasurementUnit}> .
              ?r owl:someValuesFrom ?dimunit .
            }}
          }}
          ?dimunit rdfs:subClassOf+ ?rr .
          ?rr owl:onProperty <{EMMO.hasDimensionString}> .
          ?rr owl:hasValue ?dimstr .
        }}
        """  # nosec
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

    def _parse_unitname(self, unitname: str) -> "Tuple[float, dict]":
        """Parse CamelCase unit name and return a multiplication factor (from
        prefixes) and a dict mapping each unit component to its power.

        """
        exp = {
            "Square": 2,
            "Cube": 3,
            "Cubic": 3,
            "Quartic": 4,
            "Quintic": 5,
            "Sextic": 6,
            "Septic": 7,
            "Heptic": 7,
            "Octic": 8,
            "Nonic": 9,
        }
        # TODO: infer prefixes from EMMO (requires inferred ontology or
        # current dev branch)
        prefixes = {
            "Quecto": 1e-30,
            "Ronto": 1e-27,
            "Yocto": 1e-24,
            "Zepto": 1e-21,
            "Atto": 1e-18,
            "Femto": 1e-15,
            "Pico": 1e-12,
            "Nano": 1e-9,
            "Micro": 1e-6,
            "Milli": 1e-3,
            "Centi": 1e-2,
            "Deci": 1e-1,
            "Deca": 1e1,
            "Hecto": 1e2,
            "Kilo": 1e3,
            "Mega": 1e6,
            "Giga": 1e9,
            "Tera": 1e12,
            "Peta": 1e15,
            "Exa": 1e18,
            "Zetta": 1e21,
            "Yotta": 1e24,
            "Ronna": 1e27,
            "Quetta": 1e30,
        }
        d = {}
        sign = power = 1
        mult = prefix = 1.0
        for token in re.split("(?<!^)(?=[A-Z])", unitname):
            if token in ("Per", "Reciprocal"):
                sign, power, prefix = -1, 1, 1.0
            elif token in exp:
                power = exp[token]
            elif token in prefixes:
                prefix = prefixes[token]
            elif token in self.units:
                mult *= prefix ** (sign * power)
                d[token] = sign * power
                power, prefix = 1, 1.0
            else:
                raise MissingUnitError(
                    f"No such unit (or prefix or degree): {token}"
                )
        return mult, d

    def _parse_units(self, include_prefixed=False) -> "dict[str, AttrDict]":
        """Parse EMMO units and return them as an iterator over named
        tuples.

        Arguments:
            include_prefixed: Whether to return prefixed units.

        Returns:
            Dict mapping unit names to AttrDicts with describing the unit.
            See the get_unit() method for details.

        """
        d = {}
        for iri in self._emmo_unit_iris(include_prefixed=include_prefixed):
            name = str(self.ts.value(iri, SKOS.prefLabel))
            description = self.ts.value(iri, EMMO.elucidation)
            if not description:
                description = self.ts.value(iri, EMMO.definition)
            dimstr = str(self._get_unit_dimension_string(iri))
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

            for unitCodeIRI in (SCHEMA.unitCode, EMMO.uneceCommonCode):
                unitCode = self.ts.value(iri, unitCodeIRI)
                if unitCode:
                    break

            d[name] = AttrDict(
                name=name,
                description=description,
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
                unitCode=str(unitCode) if unitCode else None,
                multiplier=float(mult[0]["value"]) if mult else None,
                offset=float(offset[0]["value"]) if offset else None,
            )
        return d

    def _parse_quantities(self, constants: bool) -> "dict[str, AttrDict]":
        """Parse EMMO quantities and return them as an iterator over named
        tuples.

        Arguments:
            constants: If true, only parse phycical constants. Otherwise,
                parse all quantities, but physical constants.

        Returns:
            Dict mapping quantity names to AttrDicts with describing the
                quantity.  See the get_quantity() method for details.
        """
        d = {}
        for iri in self._emmo_quantity_iris(constants=constants):
            name = str(self.ts.value(iri, SKOS.prefLabel))
            description = self.ts.value(iri, EMMO.elucidation)
            if not description:
                description = self.ts.value(iri, EMMO.definition)
            dimstr = str(self._get_quantity_dimension_string(iri))
            dimension = self._parse_dimension_string(dimstr)
            qudtIRI = self.ts.value(iri, EMMO.qudtReference, any=True)
            omIRI = self.ts.value(iri, EMMO.omReference, any=True)
            iupacIRI = self.ts.value(iri, EMMO.iupacReference, any=True)
            iso80000Ref = self.ts.value(iri, EMMO.ISO80000Reference, any=True)

            d[name] = AttrDict(
                name=name,
                description=description,
                aliases=[
                    str(s) for s in self.ts.value(iri, SKOS.altLabel, any=None)
                ],
                dimension=dimension,
                emmoIRI=iri,
                qudtIRI=str(qudtIRI) if qudtIRI else None,
                omIRI=str(omIRI) if omIRI else None,
                iupacIRI=str(iupacIRI) if iupacIRI else None,
                iso80000Ref=str(iso80000Ref) if iso80000Ref else None,
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

        Arguments:
            name: Search for unit by name. May also be an IRI. Ex: "Ampere"
            symbol: Search for unit by symbol or UCUM code. Ex: "A", "km"
            iri: Search for unit by IRI.
            unitCode: Search for unit by UNECE common code. Ex: "MTS"

        Returns:
            dict: A dict with attribute access describing the unit. The dict
            has the following keys:

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

        if not iri and name and ":" in name:  # allow name to be an IRI
            r = urlparse(name)
            if r.scheme and r.netloc:
                iri = name

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
        # TODO: infer from ontology
        content: list = [
            "# Pint units definitions file",
            (
                f"# Created with tripper.units from {self.formalisation} "
                f"- {self.name}"
            ),
            "",
            "@defaults",
            "    group = international",
            "    system = SI",
            "@end",
            "",
            "# Decimal prefixes",
            "Quecto- = 1e-30 = q-",
            "Ronto- = 1e-27 = r-",
            "Yocto- = 1e-24 = y-",
            "Zepto- = 1e-21 = z-",
            "Atto- =  1e-18 = a-",
            "Femto- = 1e-15 = f-",
            "Pico- =  1e-12 = p-",
            "Nano- =  1e-9  = n-",
            "Micro- = 1e-6  = µ- = μ- = u-",
            "Milli- = 1e-3  = m-",
            "Centi- = 1e-2  = c-",
            "Deci- =  1e-1  = d-",
            "Deca- =  1e+1  = da- = deka-",
            "Hecto- = 1e2   = h-",
            "Kilo- =  1e3   = k-",
            "Mega- =  1e6   = M-",
            "Giga- =  1e9   = G-",
            "Tera- =  1e12  = T-",
            "Peta- =  1e15  = P-",
            "Exa- =   1e18  = E-",
            "Zetta- = 1e21  = Z-",
            "Yotta- = 1e24  = Y-",
            "Ronna- = 1e27  = R-",
            "Quetta- = 1e30 = Q-",
            "",
            "# Binary prefixes",
            "Kibi- = 2**10 = Ki-",
            "Mebi- = 2**20 = Mi-",
            "Gibi- = 2**30 = Gi-",
            "Tebi- = 2**40 = Ti-",
            "Pebi- = 2**50 = Pi-",
            "Exbi- = 2**60 = Ei-",
            "Zebi- = 2**70 = Zi-",
            "Yobi- = 2**80 = Yi-",
            "",
            "# Base units",
            "Second = [Time] = s = second",
            "Metre = [Length] = m = metre = meter",
            # Note: gram is used instead of kilogram to get prefixes right...
            "Gram = [Mass] = g = gram",
            "Ampere = [ElectricCurrent] = A = ampere",
            "Kelvin = [ThermodynamicTemperature]; offset: 0 = K = kelvin",
            "Mole = [AmountOfSubstance] = mole = mol",
            "Candela = [LuminousIntensity] = cd = candela",
            "",
            "# Units",
            "Kilogram = 1000*Gram = kg = kilogram",
        ]

        # Regex that converts "CamelCase" to "snake_case".
        # Keeps a sequence of uppercase together.
        # Ex: HTTPResponseCodeXYZ -> http_response_code_xyz
        snake_pattern = re.compile(
            r"(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])"
        )

        # Units
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
                        f"offset: {-unit.offset}"
                    ]
                elif unit.multiplier:
                    s = [f"{unit.name} = {mult}{baseexpr}"]
                elif unit.offset:
                    s = [f"{unit.name} = {baseexpr}; offset: {-unit.offset}"]
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

            for code in [unit.unitCode] + unit.ucumCodes:
                if code and f" = {code}" not in s:
                    # code = re.sub(r"([a-zA-Z])([0-9+-])", r"\1^\2", code)
                    s.append(f" = {code}")

            # IRIs cannot be added to unit registry since they contain
            # invalid characters like ':', '/' and '#'.
            #
            # for iri in unit.emmoIRI, unit.qudtIRI, unit.omIRI:
            #     if iri and f" = {iri}" not in s:
            #         s.append(f" = {iri}")

            content.append("".join(s))

        # Quantities
        content.append("")
        content.append("# Quantities:")
        dimensions = [getattr(Dimension, d).__doc__ for d in Dimension._fields]
        for q in self.quantities.values():
            if q.name in dimensions:
                continue
            expr = [
                f"[{dim}]" if exp == 1 else f"[{dim}]**{exp}"
                for dim, exp in zip(dimensions, q.dimension)
                if exp
            ]
            content.append(f"[{q.name}] = " + " * ".join(expr))

        # Constants
        # TODO: Add physical constants. See the PINT constants_en.txt file.

        # Unit systems
        content.extend(
            [
                "",
                "# Unit systems:",
                "@system SI",
                "    Second",
                "    Metre",
                "    Kilogram",
                "    Ampere",
                "    Kelvin",
                "    Mole",
                "    Candela",
                "@end",
            ]
        )

        with open(filename, "wt", encoding="utf-8") as f:
            f.write("\n".join(content) + "\n")

    def clear_cache(self) -> None:
        """Clear caches used by this Units object."""
        cachefile = self.cachefile
        if cachefile.exists():
            cachefile.unlink()

        tsfile = self.cachedir / f"{self.name}.ntriples"
        if tsfile.exists():
            tsfile.unlink()


# pylint: disable=too-many-ancestors
class Unit(pint.Unit):
    """A subclass of pint.Unit with additional methods and properties."""

    def _get_info(self) -> dict:
        """Return a dict with attribute access describing the unit.

        SeeAlso:
            tripper.units.UnitRegistry.get_unit_info()
        """
        ureg = self._REGISTRY
        return ureg.get_unit_info(str(self))

    info = property(
        lambda self: self._get_info(),
        doc="Dict with attribute access describing this unit.",
    )
    name = property(
        lambda self: self._get_info().name,
        doc="Preferred label of the unit in the ontology.",
    )
    emmoIRI = property(
        lambda self: self._get_info().emmoIRI,
        doc="IRI of the unit in the EMMO ontology.",
    )
    qudtIRI = property(
        lambda self: self._get_info().qudtIRI,
        doc="IRI of the unit in the QUDT ontology.",
    )
    omIRI = property(
        lambda self: self._get_info().omIRI,
        doc="IRI of the unit in the OM ontology.",
    )


class Quantity(pint.Quantity):
    """A subclass of pint.Quantity with support for tripper.units."""

    def _get_dimension(self) -> Dimension:
        """Return a Dimension object with the dimensionality of this
        quantity.
        """

        def asint(x):
            """Convert floats close to whole integers to int."""
            return int(x) if abs(int(x) - x) < 1e-7 else x

        q = self.to_base_units()
        return Dimension(
            *tuple(
                asint(
                    q.u.dimensionality.get(
                        f"[{getattr(Dimension, dim).__doc__}]", 0
                    )
                )
                for dim in Dimension._fields
            )
        )

    def to_ontology_units(self) -> "Quantity":
        """Return new quantity rescale to a unit with the same
        dimensionality that exists in the ontology.
        """
        # pylint: disable=protected-access
        ureg = self._REGISTRY

        try:
            return self.m * ureg.get_unit(symbol=f"{self.u:~P}")
        except (MissingUnitError, pint.OffsetUnitCalculusError):
            pass

        units = ureg._get_tripper_units()
        dim = self._get_dimension()
        compatible_units = []
        for info in units.units.values():
            if info.dimension == dim:
                q = self.to(info.name)
                try:
                    d = units._parse_unitname(info.name)
                except MissingUnitError:
                    pass
                else:
                    compatible_units.append((info.name, q.m, d))

        def sortkey(x):
            """Returns sort key for `compatible_units`."""
            # This function prioritise compact unit expression with
            # small exponents.  Lower priority is given to pre-factor
            # close to five.
            _, m, (_, d) = x
            return 100 * sum(abs(v) for v in d.values()) + abs(
                math.log10(m / 5)
            )

        compatible_units.sort(key=sortkey)
        name, mult, _ = compatible_units[0]
        return mult * ureg[name]

    def ito_ontology_units(self) -> None:
        """Inplace rescale to ontology units."""
        q = self.to_ontology_units()
        self.ito(q.u)

    dimension = property(
        lambda self: self._get_dimension(),
        doc="Named tuple with the SI dimensionality of the quantity.",
    )


class UnitRegistry(pint.UnitRegistry):
    """A subclass of pint.UnitRegistry with support for loading units
    from ontologies.
    """

    Unit: "TypeAlias" = Unit
    Quantity: "TypeAlias" = Quantity

    def __init__(
        self,
        *args: "Any",
        ts: "Optional[Triplestore]" = None,
        url: "Optional[Union[str, Path]]" = None,
        format: "Optional[str]" = None,  # pylint: disable=redefined-builtin
        name: "Optional[str]" = None,
        formalisation: str = "emmo",
        include_prefixed: bool = False,
        cache: "Optional[bool]" = True,
        **kwargs: "Any",
    ) -> None:
        # FIXME: Remove doctest SKIP comments when support for
        # Python 3.8 is dropped
        """Initialise a Units class from triplestore `ts`

        Arguments:
            args: Positional arguments passed to pint.UnitRegistry().
            ts: Triplestore object containing the ontology to load
                units from.
            url: URL (or path) to triplestore from where to load the unit
                definitions if `ts` is not given.
                Default: "https://w3id.org/emmo/{EMMO_VERSION}"
            format: Optional format of the source referred to by `url`.
            name: A (versioned) name for the triplestore. Used for caching.
                Ex: "emmo-1.0.0".
            formalisation: The ontological formalisation with which units
                and quantities are represented. Currently only "emmo" is
                supported.
            include_prefixed: Whether to also include prefixed units.
            cache: Whether to cache the unit table. If `cache` is:
                - True: Load cache if it exists, otherwise create new cache.
                - False: Don't load cache, but (over)write new cache.
                - None: Don't use cache.
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
        self._tripper_cachedir = get_cachedir(create=cache is not None)
        self._tripper_units = None
        self._tripper_unitsargs = {
            "ts": ts,
            "url": url,
            "format": format,
            "name": name,
            "formalisation": formalisation,
            "include_prefixed": include_prefixed,
            "cache": cache,
        }
        unitsfile = self._tripper_cachedir / f"units-{name}.txt"
        self._tripper_unitsfile = unitsfile

        # If no explicit `filename` is not provided, ensure that an unit
        # definition file has been created and assign `filename` to it.
        if "filename" not in kwargs:
            kwargs["filename"] = unitsfile
            if not unitsfile.exists():
                units = self._get_tripper_units()
                units.write_pint_units(unitsfile)

        if cache:
            kwargs.setdefault("cache_folder", self._tripper_cachedir)

        super().__init__(*args, **kwargs)

    def parse_units(  # pylint: disable=arguments-differ
        self, units, *args, **kwargs
    ):
        try:
            return super().parse_units(units, *args, **kwargs)
        except pint.UndefinedUnitError:
            pass
        info = self.get_unit_info(symbol=units)
        return super().parse_units(info.name, *args, **kwargs)

    def _get_tripper_units(self) -> Units:
        """Returns a tripper.units.Units instance for the current ontology."""
        if not self._tripper_units:
            self._tripper_units = Units(
                **self._tripper_unitsargs  # type: ignore
            )
        return self._tripper_units  # type: ignore

    def get_unit(
        self,
        name: "Optional[str]" = None,
        symbol: "Optional[str]" = None,
        iri: "Optional[str]" = None,
        unitCode: "Optional[str]" = None,
    ) -> "Any":
        """Return unit matching any of the arguments.

        Arguments:
            name: Search for unit by name. May also be an IRI. Ex: "Ampere".
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

        Arguments:
            name: Search for unit by name. May also be an IRI. Ex: "Ampere"
            symbol: Search for unit by symbol or UCUM code. Ex: "A", "km"
            iri: Search for unit by IRI.
            unitCode: Search for unit by UNECE common code. Ex: "MTS"

        Returns:
            dict: A dict with attribute access describing the unit.
            The dict has the following keys:

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

    def load_quantity(self, ts: Triplestore, iri: str) -> Quantity:
        """Load quantity from triplestore.

        Arguments:
            ts: Triplestore to load from.
            iri: IRI of quantity to load.

        Returns:
            Quantity: Pint representation of the quantity.

        """
        value, unit = load_emmo_quantity(ts, iri)
        u = self.get_unit(iri=unit) if ":" in unit else self[unit]
        return value * u

    def save_quantity(
        self,
        ts: Triplestore,
        q: Quantity,
        iri: str,
        type: "Optional[str]" = None,  # pylint: disable=redefined-builtin
        tbox: bool = False,
        si_datatype: bool = True,
        annotations: "Optional[dict]" = None,
    ) -> None:
        """Save quantity to triplestore.

        Arguments:
            ts: Triplestore to save to.
            q: Quantity to save.
            iri: IRI of the quantity in the triplestore.
            type: IRI of the type or superclass (if `tbox` is true) of the
                quantity.
            tbox: Whether to document the quantity in the tbox.
            si_datatype: Whether to represent the value using the
                `emmo:SIQuantityDatatype` datatype.
            annotations: Additional annotations describing the quantity.
                Use Literal() for literal annotations.

        """
        save_emmo_quantity(
            ts=ts,
            q=q,
            iri=iri,
            type=type,
            tbox=tbox,
            si_datatype=si_datatype,
            annotations=annotations,
        )

    def clear_cache(self):
        """Clear caches related to this unit registry."""
        if self._tripper_unitsfile.exists():
            self._tripper_unitsfile.unlink()

        name = self._tripper_unitsargs["name"]
        include_prefixed = self._tripper_unitsargs["include_prefixed"]
        pf = "-prefixed" if include_prefixed else ""
        cachedir = self._tripper_cachedir
        ontofile = cachedir / f"{name}.ntriples"
        unitsfile = cachedir / f"units{pf}-{name}.pickle"
        if ontofile.exists():
            ontofile.unlink()
        if unitsfile.exists():
            unitsfile.unlink()

    def set_as_default(self) -> "Union[UnitRegistry, None]":
        """Set current unit registry as the default one.

        This unit registry can then be accessed with `get_ureg()`.

        Returns the previous default unit registry."""
        global _unit_reg  # pylint: disable=global-statement
        old = _unit_reg
        _unit_reg = self
        return old
