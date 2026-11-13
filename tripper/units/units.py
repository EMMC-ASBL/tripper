"""A module for handling units using EMMO as the main resource.

Pint is used for programatic unit conversions.
"""

import math
import pickle
import re
import sys
import warnings
from collections import defaultdict, deque, namedtuple
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
from tripper.namespace import atomic_write, get_cachedir
from tripper.utils import AttrDict, bnode_iri

if TYPE_CHECKING:  # pragma: no cover
    from collections.abc import Generator
    from pathlib import Path
    from typing import (
        Any,
        Optional,
        Union,
    )

    from pint.compat import TypeAlias


# Default EMMO version
EMMO_VERSION = "1.1.0"

# EMMO namespace IRI (the same for all versions of EMMO)
EMMO_IRI = "https://w3id.org/emmo#"

# Some EMMO properties used by this module were renamed in EMMO 1.0.4,
# while keeping their IRI.  Refer to them by IRI, such that this module
# works with all versions of EMMO.
NUMBER_VALUE = EMMO_IRI + "EMMO_faf79f53_749d_40b2_807c_d34244c192f4"
"""emmo:numberValue (named emmo:hasNumberValue before EMMO 1.0.4)."""

# Only defined in EMMO 1.0.3 and earlier
SI_QUANTITY_VALUE = EMMO_IRI + "EMMO_42806efc_581b_4ff8_81b0_b4d62153458b"
"""emmo:hasSIQuantityValue (removed in EMMO 1.0.4)."""

# Cached module variables
_unit_ts: "dict[str, Triplestore]" = {}  # Unit triplestores, by name
_unit_ns: "dict[str, Namespace]" = {}  # Unit namespaces, by name
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


class MissingQuantityError(UnitError):
    """Quantity not found in ontology."""


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
    arguments.  E.g. `get_ureg(emmo_version="1.0.3")` creates a default
    unit registry for EMMO 1.0.3.

    """
    global _unit_reg
    if not _unit_reg:
        if nocreate:
            raise NoDefaultUnitRegistryError("No default unit registry")
        ureg = UnitRegistry(*args, **kwargs)
        _unit_reg = ureg
    else:
        ureg = _unit_reg
    return ureg


def _default_url_name(url, name, emmo_version=None) -> tuple:
    """Return default unit triplestore url and name.

    If `url` is not given, it defaults to the given version of EMMO, or
    to `EMMO_VERSION` if `emmo_version` is not given.
    """
    if url is None:
        version = emmo_version if emmo_version else EMMO_VERSION
        url = f"https://w3id.org/emmo/{version}"
        if not name:
            name = f"emmo-{version}"
    elif emmo_version:
        raise ValueError("`url` and `emmo_version` cannot both be given")
    elif not name:
        raise ValueError("`name` must be given with `url`")
    return url, name


def get_unit_triplestore(
    url: "Optional[Union[str, Path]]" = None,
    format: "Optional[str]" = None,
    name: "Optional[str]" = None,
    cache: "Union[bool, None]" = True,
    emmo_version: "Optional[str]" = None,
) -> Triplestore:
    """Return, potentially cached, triplestore object that defines the units.

    Arguments:
        url: URL or path to unit triplestore.
            Default: "https://w3id.org/emmo/{emmo_version}"
        format: Optional format of the source referred to by `url`.
        name: A (versioned) name for the triplestore. Used for caching.
            Ex: "emmo-1.0.0".
        cache: Whether to load from cache. If `cache` is:
            - True: Load cache if it exists, otherwise create new cache.
            - False: Don't load cache, but (over)write new cache.
            - None: Don't use cache.
        emmo_version: Version of EMMO to load units from if `url` is not
            given.  Defaults to `EMMO_VERSION`.

    """
    url, name = _default_url_name(url, name, emmo_version)
    if name not in _unit_ts:
        ts = Triplestore("rdflib")
        cachefile = get_cachedir() / f"units-{name}.ntriples"
        if cache and cachefile.exists():
            ts.parse(cachefile, format="ntriples")
        else:
            print(  # noqa: T201
                "* caching units triplestore... ",
                end="",
                flush=True,
                file=sys.stderr,
            )
            ts.parse(url, format=format)
            print("done", file=sys.stderr)  # noqa: T201
            if cache is not None:
                try:
                    with atomic_write(cachefile) as tmp:
                        ts.serialize(tmp, format="ntriples", encoding="utf-8")
                except PermissionError as exc:
                    warnings.warn(
                        f"{exc}: {cachefile}",
                        category=PermissionWarning,
                    )
        _unit_ts[name] = ts
    return _unit_ts[name]


def get_unit_namespace(
    url: "Optional[Union[str, Path]]" = None,
    format: "Optional[str]" = None,
    name: "Optional[str]" = None,
    cache: "Union[bool, None]" = True,
    emmo_version: "Optional[str]" = None,
) -> Namespace:
    """Return, potentially cached, EMMO namespace for the unit triplestore.

    Unlike `tripper.EMMO`, which looks up labels in the latest version of
    EMMO, labels of the returned namespace are looked up in the given
    version of EMMO.  This matters, since some IRIs differ between
    versions of EMMO.

    Arguments:
        url: URL or path to unit triplestore.
            Default: "https://w3id.org/emmo/{emmo_version}"
        format: Optional format of the source referred to by `url`.
        name: A (versioned) name for the triplestore. Used for caching.
            Ex: "emmo-1.0.0".
        cache: Whether to load the triplestore from cache.  See
            get_unit_triplestore().
        emmo_version: Version of EMMO to load units from if `url` is not
            given.  Defaults to `EMMO_VERSION`.

    Returns:
        EMMO namespace object with label lookup in the unit triplestore.
    """
    url, name = _default_url_name(url, name, emmo_version)
    if name not in _unit_ns:
        ts = get_unit_triplestore(
            url=url, format=format, name=name, cache=cache
        )
        _unit_ns[name] = _create_unit_namespace(ts, name)
    return _unit_ns[name]


def _create_unit_namespace(ts: Triplestore, name: str) -> Namespace:
    """Return EMMO namespace with label lookup in triplestore `ts`.

    The label cache is named after `name`, such that it is not shared
    with `tripper.EMMO` or namespaces for other versions of EMMO.
    """
    return Namespace(
        iri=EMMO_IRI,
        label_annotations=True,
        check=True,
        triplestore=ts,
        cachename=f"namespace-{name}",
    )


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


def load_emmo_quantity(ts: Triplestore, iri: str) -> "tuple[float, str]":
    """Return value and unit for EMMO quantity with given `iri`.

    The quantity may either be an individual or a class, in which case
    the value and unit are given with value restrictions.

    The following representations of quantities are supported:

    - `emmo:hasNumericalPart` (or `emmo:numberValue`) for the value and
      `emmo:hasMeasurementUnit`, `emmo:hasReferencePart` or
      `emmo:hasMetrologicalReference` for the unit.  The unit is returned
      as an IRI.
    - `emmo:hasSIQuantityValue` (EMMO 1.0.3 and earlier), with the value
      and unit as a literal, like "2 mm".  The unit is returned as a
      symbol.

    """
    isclass = ts.query(f"ASK {{<{iri}> a owl:Class}}")

    def pattern(prop: str, var: str) -> str:
        """Return SPARQL pattern relating the quantity to `?var` via
        property `prop`."""
        if isclass:
            r = f"?r_{var}"
            return (
                f"<{iri}> rdfs:subClassOf+ {r} . "
                f"{r} owl:onProperty <{prop}> . "
                f"{r} owl:hasValue|owl:someValuesFrom ?{var} ."
            )
        return f"<{iri}> <{prop}> ?{var} ."

    def first(query: str) -> "Any":
        """Return first value returned by `query` or None."""
        result = ts.query(query)
        return result[0][0] if result else None  # type: ignore

    # Check for emmo:hasSIQuantityValue
    qval = first(f"SELECT ?v WHERE {{ {pattern(SI_QUANTITY_VALUE, 'v')} }}")
    if qval:
        m = re.match(
            r"([+-]?[0-9]*\.?[0-9]*([eE][+-]?[0-9]+)?)[ *⋅]*(.*)?", str(qval)
        )
        if m:
            value, _, unit = m.groups()
            return float(value), unit

    # Check for emmo:hasNumericalPart (or emmo:numberValue) and unit
    value = first(f"""
    SELECT ?v WHERE {{
      {{ {pattern(EMMO.hasNumericalPart, "num")} ?num <{NUMBER_VALUE}> ?v . }}
      UNION
      {{ {pattern(NUMBER_VALUE, "v")} }}
    }}
    """)
    unit = first(f"""
    SELECT ?v WHERE {{
      {{ {pattern(EMMO.hasMeasurementUnit, "v")} }}
      UNION
      {{ {pattern(EMMO.hasReferencePart, "v")} }}
      UNION
      {{ {pattern(EMMO.hasMetrologicalReference, "v")} }}
    }}
    """)
    if value is None or unit is None:
        raise UnitError(f"cannot find value and unit of quantity: {iri}")
    return float(value), str(unit)


def save_emmo_quantity(
    ts: Triplestore,
    q: "Quantity",
    iri: str,
    type: "Optional[str]" = None,
    tbox: bool = False,
    si_datatype: "Optional[bool]" = None,
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
            `emmo:SIQuantityDatatype` datatype.  This datatype was removed
            in EMMO 1.0.4.  The default is to use it with the versions of
            EMMO that support it.
        annotations: Additional annotations describing the quantity.
            Use Literal() for literal annotations.

    Notes:
        With EMMO 1.0.4 and later, the quantity is represented with
        `emmo:hasNumericalPart` and `emmo:hasMeasurementUnit`, where the
        unit is an individual.  With earlier versions,
        `emmo:hasReferencePart` is used, since units are classes.

    """
    units = q._REGISTRY._get_tripper_units()
    ns = units.ns
    if si_datatype is None:
        si_datatype = not units.units_are_individuals
    elif si_datatype and units.units_are_individuals:
        raise UnitError(
            "emmo:SIQuantityDatatype is not supported by EMMO version used "
            f"by the unit registry: {units.name}"
        )

    if EMMO not in ts.namespaces.values():
        ts.bind("emmo", EMMO)

    if ts.has(iri):
        raise IRIExistsError(iri)

    if not type:
        type = ns.Quantity

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
                    (r, OWL.onProperty, SI_QUANTITY_VALUE),
                    (r, OWL.hasValue, Literal(q)),
                ]
            )
        else:
            v = bnode_iri("value")
            r2 = bnode_iri("restriction")
            q2 = q.to_ontology_units()
            triples.extend(
                [
                    (r, OWL.onProperty, ns.hasNumericalPart),
                    (r, OWL.hasValue, v),
                    (v, RDF.type, ns.Numerical),
                    (v, NUMBER_VALUE, Literal(q2.m)),
                    (iri, RDFS.subClassOf, r2),
                    (r2, RDF.type, OWL.Restriction),
                ]
            )
            if units.units_are_individuals:
                triples.extend(
                    [
                        (r2, OWL.onProperty, ns.hasMeasurementUnit),
                        (r2, OWL.hasValue, q2.u.emmoIRI),
                    ]
                )
            else:
                triples.extend(
                    [
                        (r2, OWL.onProperty, ns.hasReferencePart),
                        (r2, OWL.someValuesFrom, q2.u.emmoIRI),
                    ]
                )
    else:
        if si_datatype:
            triples.append((iri, SI_QUANTITY_VALUE, Literal(q)))
        else:
            v = bnode_iri("value")
            q2 = q.to_ontology_units()
            unitprop = (
                ns.hasMeasurementUnit
                if units.units_are_individuals
                else ns.hasReferencePart
            )
            triples.extend(
                [
                    (iri, ns.hasNumericalPart, v),
                    (v, RDF.type, ns.Numerical),
                    (v, NUMBER_VALUE, Literal(q2.m)),
                    (iri, unitprop, q2.u.emmoIRI),
                ]
            )

    if annotations:
        for pred, obj in annotations.items():
            triples.append((iri, pred, obj))

    ts.add_triples(triples)


class Units:
    """A class representing all units in an ontology."""

    def __init__(
        self,
        ts: "Optional[Triplestore]" = None,
        url: "Optional[Union[str, Path]]" = None,
        format: "Optional[str]" = None,
        name: "Optional[str]" = None,
        formalisation: str = "emmo",
        include_prefixed: bool = False,
        cache: "Union[bool, None]" = True,
        emmo_version: "Optional[str]" = None,
    ) -> None:
        """Initialise a Units class from triplestore `ts`

        Arguments:
            ts: Triplestore object containing the ontology to load
                units from.
            url: URL (or path) to the ontology from where unit
                definitions are loaded if `ts` is not given.
                Default: "https://w3id.org/emmo/{emmo_version}"
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
            emmo_version: Version of EMMO to load units from if neither
                `ts` nor `url` are given.  Defaults to `EMMO_VERSION`.

        Attributes:
            ns: EMMO namespace with label lookup in the unit ontology.
                Use it instead of `tripper.EMMO`, since some IRIs differ
                between versions of EMMO.
            units_are_individuals: Whether units are individuals (EMMO
                1.0.4 and later) or classes (EMMO 1.0.3 and earlier).

        """
        url, name = _default_url_name(url, name, emmo_version)

        if ts:
            self.ts = ts
            self.ns = _create_unit_namespace(ts, name)
        else:
            self.ts = get_unit_triplestore(
                url=url, format=format, name=name, cache=cache
            )
            self.ns = get_unit_namespace(
                url=url, format=format, name=name, cache=cache
            )

        # Created on demand by _get_dimension_maps()
        self._dimension_maps: Optional[tuple[dict, dict, dict]] = None

        # EMMO 1.0.4 changed units from classes to individuals
        self.units_are_individuals = self.ts.has(
            EMMO_IRI + "Metre", RDF.type, OWL.NamedIndividual
        )

        pf = "-prefixed" if include_prefixed else ""
        fname = f"units{pf}-{name}.pickle"
        cachedir = get_cachedir(create=True)
        cachefile = cachedir / fname
        if cache and cachefile.exists():
            with open(cachefile, "rb") as f:
                d = pickle.load(f)  # noqa: S301
                self.units = d["units"]
                self.quantities = d["quantities"]
                self.constants = d["constants"]
        else:
            print("* caching units... ", end="", flush=True, file=sys.stderr)  # noqa: T201
            self.units = self._parse_units(include_prefixed=include_prefixed)
            print(  # noqa: T201
                "done\n* caching quantities... ",
                end="",
                flush=True,
                file=sys.stderr,
            )
            self.quantities = self._parse_quantities(constants=False)
            print(  # noqa: T201
                "done\n* caching constants... ",
                end="",
                flush=True,
                file=sys.stderr,
            )
            self.constants = self._parse_quantities(constants=True)
            print("done", file=sys.stderr)  # noqa: T201

            if cache is not None:
                d = {
                    "units": self.units,
                    "quantities": self.quantities,
                    "constants": self.constants,
                }
                with atomic_write(cachefile) as tmp, open(tmp, "wb") as f:
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
        if self.units_are_individuals:
            # A unit is an individual with a dimension string inherited
            # from its type
            dimstrs = self._get_dimension_maps()[1]
            units = []
            for iri, _, _ in self.ts.triples(
                predicate=RDF.type, object=OWL.NamedIndividual
            ):
                classes = set(self._superclasses(iri))
                if not any(cls in dimstrs for cls in classes):
                    continue
                if include_prefixed or self.ns.PrefixedUnit not in classes:
                    units.append(iri)
            return sorted(units)

        prefixfilter = (
            ""
            if include_prefixed
            else (
                "FILTER NOT EXISTS "
                f"{{ ?unit rdfs:subClassOf <{self.ns.PrefixedUnit}> . }}"
            )
        )
        query = f"""
        PREFIX rdfs: <{RDFS}>
        SELECT ?unit
        WHERE {{
          ?unit rdfs:subClassOf+ ?dimunit .
          ?dimunit rdfs:subClassOf ?r .
          ?r owl:onProperty <{self.ns.hasDimensionString}> .
          {prefixfilter}
        }}
        """
        # Bug in mupy... seems to be fixed in master
        return [iri for (iri,) in self.ts.query(query)]  # type: ignore

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
          ?r owl:onProperty <{self.ns.hasMeasurementUnit}> .
          FILTER {constonly} EXISTS {{
            ?q rdfs:subClassOf+ <{self.ns.PhysicalConstant}> .
          }}
          FILTER (!isBlank(?q))
        }}
        """
        # Bug in mupy... seems to be fixed in master
        return [iri for (iri,) in self.ts.query(query)]  # type: ignore

    def _get_unit_symbols(self, iri: str) -> list:
        """Return a list with unit symbols for unit with the given IRI.

        Symbols from `emmo:unitSymbolValue` come first, followed by
        symbols from annotations.  Within each group, symbols are sorted,
        since the iteration order of the triplestore may differ between
        processes.
        """
        if self.units_are_individuals:
            symbols = sorted(
                str(symbol)
                for symbol in self.ts.value(
                    iri, self.ns.unitSymbolValue, any=None
                )
            )
        else:
            symbols = sorted(
                str(r["value"])
                for r in self.ts.restrictions(
                    iri, self.ns.unitSymbolValue, type="value"
                )
            )
        annotated = sorted(
            str(symbol)
            for symbol in self.ts.value(iri, self.ns.unitSymbol, any=None)
        )
        symbols.extend(f"1{s}" if s.startswith("/") else s for s in annotated)
        return symbols

    def _get_dimension_maps(self) -> "tuple[dict, dict, dict]":
        """Return dicts used for looking up dimension strings.

        Returns a tuple of three dicts:
            - parents: maps a class to a sorted list of its direct
              superclasses (rdfs:subClassOf) and an individual to its
              types (rdf:type).
            - dimstrs: maps a hasDimensionString restriction to its
              dimension string.
            - measurement_units: maps a hasMeasurementUnit restriction to
              its unit (owl:someValuesFrom).

        The dicts are created on first call by reading the triplestore
        once.  This is much faster than doing a SPARQL query with a
        `rdfs:subClassOf+` property path for every unit and quantity.
        """
        maps = self._dimension_maps
        if maps is None:
            parents: dict[str, list] = {}
            for s, _, o in self.ts.triples(predicate=RDFS.subClassOf):
                parents.setdefault(s, []).append(o)
            for s, _, o in self.ts.triples(predicate=RDF.type):
                if not o.startswith(str(OWL)):
                    parents.setdefault(s, []).append(o)
            for superclasses in parents.values():
                superclasses.sort()

            onprop = {
                s: o for s, _, o in self.ts.triples(predicate=OWL.onProperty)
            }
            dimstr_prop = self.ns.hasDimensionString
            dimstrs = {
                s: o
                for s, _, o in self.ts.triples(predicate=OWL.hasValue)
                if onprop.get(s) == dimstr_prop
            }
            unit_prop = self.ns.hasMeasurementUnit
            measurement_units = {
                s: o
                for s, _, o in self.ts.triples(predicate=OWL.someValuesFrom)
                if onprop.get(s) == unit_prop
            }
            maps = (parents, dimstrs, measurement_units)
            self._dimension_maps = maps
        return maps

    def _superclasses(self, iri: str) -> "Generator[str, None, None]":
        """Generate all superclasses of `iri` (rdfs:subClassOf+) in
        breadth-first order.

        If `iri` is an individual, its types and their superclasses are
        generated."""
        parents = self._get_dimension_maps()[0]
        visited = set()
        queue = deque(parents.get(iri, ()))
        while queue:
            cls = queue.popleft()
            if cls not in visited:
                visited.add(cls)
                yield cls
                queue.extend(parents.get(cls, ()))

    def _get_unit_dimension_string(self, iri: str) -> str:
        """Return the dimension string for unit with the given IRI."""
        dimstrs = self._get_dimension_maps()[1]
        for cls in self._superclasses(iri):
            if cls in dimstrs:
                return dimstrs[cls]
        raise MissingDimensionStringError(iri)

    def _get_quantity_dimension_string(self, iri: str) -> str:
        """Return the dimension string for quantity with the given IRI."""
        measurement_units = self._get_dimension_maps()[2]
        for cls in self._superclasses(iri):
            if cls in measurement_units:
                try:
                    return self._get_unit_dimension_string(
                        measurement_units[cls]
                    )
                except MissingDimensionStringError:
                    pass
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

    def _parse_unitname(self, unitname: str) -> "tuple[float, dict]":
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
            description = self._get_description(iri)
            dimstr = str(self._get_unit_dimension_string(iri))
            dimension = self._parse_dimension_string(dimstr)
            mult = self._get_unit_value(iri, self.ns.hasSIConversionMultiplier)
            offset = self._get_unit_value(iri, self.ns.hasSIConversionOffset)
            # A missing multiplier means one, except for non-SI units,
            # whose conversion to SI then is unknown.  Units with no
            # multiplier and offset are regarded as SI coherent, since
            # older versions of EMMO don't classify all SI units as such.
            classes = set(self._superclasses(iri))
            non_si = self.ns.NonSIUnit in classes
            if mult is None and not non_si:
                mult = 1.0
            coherent = self.ns.SICoherentUnit in classes or (
                not non_si and mult == 1.0 and not offset
            )
            qudtIRI = self.ts.value(iri, self.ns.qudtReference, any=True)
            omIRI = self.ts.value(iri, self.ns.omReference, any=True)

            for unitCodeIRI in (SCHEMA.unitCode, self.ns.uneceCommonCode):
                unitCode = self.ts.value(iri, unitCodeIRI)
                if unitCode:
                    break

            d[name] = AttrDict(
                name=name,
                description=description,
                # Sort, since the iteration order of the triplestore may
                # differ between processes
                aliases=sorted(
                    str(s) for s in self.ts.value(iri, SKOS.altLabel, any=None)
                ),
                symbols=self._get_unit_symbols(iri),
                dimension=dimension,
                emmoIRI=iri,
                qudtIRI=str(qudtIRI) if qudtIRI else None,
                omIRI=str(omIRI) if omIRI else None,
                ucumCodes=sorted(
                    str(s)
                    for s in self.ts.value(iri, self.ns.ucumCode, any=None)
                ),
                unitCode=str(unitCode) if unitCode else None,
                multiplier=float(mult) if mult is not None else None,
                offset=float(offset) if offset is not None else None,
                coherent=coherent,
                siAccepted=self.ns.SIAcceptedUnit in classes,
            )
        return d

    def _get_description(self, iri: str) -> "Optional[str]":
        """Return elucidation or definition of `iri`."""
        description = self.ts.value(iri, self.ns.elucidation, any=True)
        if not description:
            description = self.ts.value(iri, self.ns.definition, any=True)
        return description

    def _get_unit_value(self, iri: str, prop: str) -> "Any":
        """Return the value of data property `prop` for the unit `iri`.

        The value is given directly if units are individuals, otherwise
        with a value restriction.  None is returned if there is no value.
        """
        if self.units_are_individuals:
            return self.ts.value(iri, prop, any=True)
        restrictions = list(self.ts.restrictions(iri, property=prop))
        return restrictions[0]["value"] if restrictions else None

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
            description = self._get_description(iri)
            try:
                dimstr = str(self._get_quantity_dimension_string(iri))
            except MissingDimensionStringError:
                # Skip general quantity classes with no dimension string
                continue
            dimension = self._parse_dimension_string(dimstr)
            qudtIRI = self.ts.value(iri, self.ns.qudtReference, any=True)
            omIRI = self.ts.value(iri, self.ns.omReference, any=True)
            iupacIRI = self.ts.value(iri, self.ns.iupacReference, any=True)
            iso80000Ref = self.ts.value(
                iri, self.ns.ISO80000Reference, any=True
            )

            d[name] = AttrDict(
                name=name,
                description=description,
                # Sort, since the iteration order of the triplestore may
                # differ between processes
                aliases=sorted(
                    str(s) for s in self.ts.value(iri, SKOS.altLabel, any=None)
                ),
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
            - multiplier: Unit multiplier.  None if the conversion to SI
              is not known.
            - offset: Unit offset.
            - coherent: Whether the unit is a SI coherent unit.
            - siAccepted: Whether the unit is accepted for use with SI.
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

        # Pint requires that symbols and aliases are unique.  Assign each
        # symbol to the first unit that claims it, in order of priority.
        # Within each round, SI coherent units take precedence, followed
        # by units accepted for use with SI.  Hence, "K" is Kelvin and not
        # Kayser.
        ordered = sorted(
            self.units.items(),
            key=lambda item: (
                not item[1].get("coherent", False),
                not item[1].get("siAccepted", False),
            ),
        )
        forbidden_chars = ".·/*-"
        table = str.maketrans(
            {"[": None, "]": None, " ": "_", "{": "_", "}": "_"}
        )
        symbolkeys: dict[str, str] = {}  # maps symbol to unit key
        realsymbols = set()  # symbols that are not codes or aliases

        def addsymbol(symbol, key, real=False):
            """Assign `symbol` to unit `key`, if it is valid and free."""
            if symbol and not any(c in symbol for c in forbidden_chars):
                symbol = symbol.translate(table)
                if symbol not in symbolkeys:
                    symbolkeys[symbol] = key
                    if real:
                        realsymbols.add(symbol)

        # Round 1: first symbol of each unit
        for key, unit in ordered:
            if unit.symbols:
                addsymbol(unit.symbols[0], key, real=True)
        # Round 2: other symbols
        for key, unit in ordered:
            for symbol in unit.symbols[1:]:
                addsymbol(symbol, key, real=True)
        # Round 3: UCUM codes and UNECE common codes
        for key, unit in ordered:
            for symbol in unit.ucumCodes + [unit.unitCode]:
                addsymbol(symbol, key)
        # Round 4: aliases (skos:altLabel)
        for key, unit in ordered:
            for alias in unit.aliases:
                addsymbol(alias, key)

        # Map unit keys to list of symbols
        symbols = defaultdict(list)
        for symbol, key in symbolkeys.items():
            symbols[key].append(symbol)

        for key, unit in self.units.items():
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
                    raise AssertionError("should never happen")
            elif baseexpr == "1":
                s = [f"{unit.name} = []"]
            else:
                s = [f"{unit.name} = {baseexpr}"]

            # The first real symbol is the Pint symbol.  Other symbols,
            # codes and labels are added as aliases.
            real = [x for x in symbols[key] if x in realsymbols]
            s.append(f" = {real[0] if real else '_'}")

            # Add snake_case name as alias, unless it is used by another unit
            snake = snake_pattern.sub("_", unit.name).lower()
            if snake != unit.name and symbolkeys.get(snake, key) == key:
                s.append(f" = {snake}")

            s.extend(
                f" = {alias}"
                for alias in symbols[key]
                if alias not in real[:1] and alias != snake
            )

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

        with open(filename, "w", encoding="utf-8") as f:
            f.write("\n".join(content) + "\n")

    def clear_cache(self) -> None:
        """Clear caches used by this Units object."""
        cachefile = self.cachefile
        if cachefile.exists():
            cachefile.unlink()

        tsfile = self.cachedir / f"{self.name}.ntriples"
        if tsfile.exists():
            tsfile.unlink()


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

        Notes:
            This function tries to select the "simplest" unit among all the
            units with compatible physical dimensionality in the ontology.

            This is done according to the following heuristics:

            1. Find units with compatible physical dimensionality in the
               ontology.
               SI coherent units and units accepted for use with SI are
               preferred.  Units with unknown conversion to SI are
               ignored.
            2. Among these units, select the unit that minimises the absolute
               value of the sum of the powers of each unit component.

               Example: among the units

                   Pa = Pa^1       -> sum=1
                   J/m^3 = J^1/m^3 -> sum=1+3=4
                   N/m^2 = N^1/m^2 -> sum=1+2=3

               Pa will be selected.
            3. If two units have the same sum, the unit that minimises
               `log10(magnitude/5)` is selected, where `magnitude` is the
               magnitude of the quantity when expressed in SI base units.
            4. Units with an UNECE common code are preferred over equally
               ranked units without.

        """
        ureg = self._REGISTRY

        try:
            return self.m * ureg.get_unit(symbol=f"{self.u:~P}")
        except (MissingUnitError, pint.OffsetUnitCalculusError):
            pass

        units = ureg._get_tripper_units()
        dim = self._get_dimension()
        compatible_units = []
        for info in units.units.values():
            # Skip units with unknown conversion to SI units
            if info.dimension == dim and info.multiplier is not None:
                q = self.to(info.name)
                try:
                    d = units._parse_unitname(info.name)
                except MissingUnitError:
                    d = 1.0, {q.u.name: 1}
                compatible_units.append((info.name, q.m, d))

        # Prefer SI coherent units and units accepted for use with SI
        preferred = [
            x
            for x in compatible_units
            if units.units[x[0]].get("coherent")
            or units.units[x[0]].get("siAccepted")
        ]
        if preferred:
            compatible_units = preferred

        def sortkey(x):
            """Returns sort key for `compatible_units`."""
            # This function prioritise compact unit expression with
            # small exponents.  Lower priority is given to pre-factor
            # close to five.
            name, m, (_, d) = x
            score = 100 * sum(abs(v) for v in d.values()) + abs(
                math.log10(m / 5)
            )
            return score, units.units[name].unitCode is None

        compatible_units.sort(key=sortkey)
        name, mult, _ = compatible_units[0]
        return ureg.Quantity(mult, name)

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
        format: "Optional[str]" = None,
        name: "Optional[str]" = None,
        formalisation: str = "emmo",
        include_prefixed: bool = False,
        cache: "Optional[bool]" = True,
        emmo_version: "Optional[str]" = None,
        **kwargs: "Any",
    ) -> None:
        """Initialise a Units class from triplestore `ts`

        Arguments:
            args: Positional arguments passed to pint.UnitRegistry().
            ts: Triplestore object containing the ontology to load
                units from.
            url: URL (or path) to triplestore from where to load the unit
                definitions if `ts` is not given.
                Default: "https://w3id.org/emmo/{emmo_version}"
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
            emmo_version: Version of EMMO to load units from if neither
                `ts` nor `url` are given.  Defaults to `EMMO_VERSION`.
                Ex: "1.0.3".
            kwargs: Keyword arguments passed to pint.UnitRegistry().

        Examples:
            >>> from tripper.units import UnitRegistry
            >>> ureg = UnitRegistry()
            >>> u = ureg.Metre
            >>> u
            <Unit('Metre')>

            >>> u.emmoIRI
            'https://w3id.org/emmo#Metre'

            >>> q = ureg.Quantity("3 h")
            >>> q
            <Quantity(3, 'Hour')>

            >>> q.u.qudtIRI
            'http://qudt.org/vocab/unit/HR'

        """
        url, name = _default_url_name(url, name, emmo_version)

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
                with atomic_write(unitsfile) as tmp:
                    units.write_pint_units(tmp)

        if cache:
            kwargs.setdefault("cache_folder", self._tripper_cachedir)

        super().__init__(*args, **kwargs)

    def parse_units(self, units, *args, **kwargs):
        """Parses a unit expression string and returns a UnitContainer object
        with canonical unit names."""
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
    ) -> "Unit":
        """Return Pint unit matching the unit name, symbol, iri or unitCode
         as defined in the ontology.

        Arguments:
            name: Search for unit by name (prefLabel). May also be an IRI.
                Ex: "Ampere".
            symbol: Search for unit by symbol or UCUM code. Ex: "A", "km"
            iri: Search for unit by IRI.
            unitCode: Search for unit by UNECE common code. Ex: "MTS"

        Returns:
            Return matching Pint unit.
        """
        info = self.get_unit_info(
            name=name, symbol=symbol, iri=iri, unitCode=unitCode
        )
        return self(info.name).u

    def get_unit_info(
        self,
        name: "Optional[str]" = None,
        symbol: "Optional[str]" = None,
        iri: "Optional[str]" = None,
        unitCode: "Optional[str]" = None,
    ) -> AttrDict:
        """Return information about a unit name, symbol, iri or unitCode
         as defined in the ontology.

        Arguments:
            name: Search for unit by name (prefLabel). May also be an IRI.
                Ex: "Ampere"
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
            - multiplier: Unit multiplier for converting to the
              corresponding SI unit.
            - offset: Unit offset for converting to the corresponding SI unit.

        """
        units = self._get_tripper_units()
        return units.get_unit(
            name=name, symbol=symbol, iri=iri, unitCode=unitCode
        )

    def get_quantity(
        self,
        name: "Optional[str]" = None,
        iri: "Optional[str]" = None,
        iso80000Ref: "Optional[str]" = None,
        value: float = 1.0,
    ) -> "Quantity":
        """Convert quantity name, iri or iso80000ref in the ontology to a Pint
        quantity object.

        Arguments:
            name: Access quantity by its name (skos:prefLabel in the ontology).
                Ex: "Energy".
            iri: Access quantity by its IRI, which may refer to EMMO, QUDT,
                OM or IUPAC.
            iso80000Ref: Access quantity by its ISO80000 reference. Ex: 5-20-1
            value: Value of the quantity value in units of SI base units.

        """
        units = self._get_tripper_units()
        if name:
            if name not in units.quantities:
                raise MissingQuantityError(name)
            info = units.quantities[name]
        elif iri:
            iri_attr = "emmoIRI", "qudtIRI", "omIRI", "iupacIRI"
            found = False
            for info in units.quantities.values():
                for attr in iri_attr:
                    if info[attr] == iri:
                        found = True
                        break
                if found:
                    break
            else:
                raise MissingQuantityError(f"iri={iri}")
        elif iso80000Ref:
            for info in units.quantities.values():
                if info.iso80000Ref == iso80000Ref:
                    break
            else:
                raise MissingQuantityError(f"iso80000Ref={iso80000Ref}")
        else:
            raise ValueError(
                "Missing argument to get_quantity(). Either `name`, "
                "`iri` or `iso80000Ref` must be provided"
            )
        q = self.Quantity(value, base_unit_expression(info.dimension))
        return q.to_ontology_units()

    def load_quantity(self, ts: Triplestore, iri: str) -> Quantity:
        """Load quantity individual or (sub)class from the triplestore.

        Arguments:
            ts: Triplestore to load from.
            iri: IRI of quantity individual to load.

        Returns:
            Quantity: Pint representation of the quantity.

        Notes:
            The quantity must have a value, hence EMMO.Energy will return
            and exception since it is defined without a value in the ontology.
        """
        value, unit = load_emmo_quantity(ts, iri)
        return self.Quantity(
            value, self.get_unit(iri=unit) if ":" in unit else unit
        )

    def save_quantity(
        self,
        ts: Triplestore,
        q: Quantity,
        iri: str,
        type: "Optional[str]" = None,
        tbox: bool = False,
        si_datatype: "Optional[bool]" = None,
        annotations: "Optional[dict]" = None,
    ) -> None:
        """Save a Pint quantity individual to triplestore.

        Arguments:
            ts: Triplestore to save to.
            q: Quantity to save.
            iri: IRI of the quantity in the triplestore.
            type: IRI of the type or superclass (if `tbox` is true) of the
                quantity.
            tbox: Whether to document the quantity in the tbox.
            si_datatype: Whether to represent the value using the
                `emmo:SIQuantityDatatype` datatype.  The default is to use
                it with the versions of EMMO that support it (EMMO 1.0.3
                and earlier).
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
        ontofile = cachedir / f"units-{name}.ntriples"
        unitsfile = cachedir / f"units{pf}-{name}.pickle"
        nsfile = cachedir / f"namespace-{name}.cache"
        for path in ontofile, unitsfile, nsfile:
            if path.exists():
                path.unlink()

    def set_as_default(self) -> "Union[UnitRegistry, None]":
        """Set current unit registry as the default one.

        This unit registry can then be accessed with `get_ureg()`.

        Returns the previous default unit registry."""
        global _unit_reg
        old = _unit_reg
        _unit_reg = self
        return old
