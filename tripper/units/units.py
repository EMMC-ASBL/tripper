"""A module for handling units using EMMO as the main resource.

Pint is used for programatic unit conversions.
"""
#from collection import namedtuple
from typing import TYPE_CHECKING

import pint

from tripper import EMMO, OWL, RDF, RDFS, SKOS, Namespace, Triplestore
from tripper.namespace import get_cachedir

if TYPE_CHECKING:  # pragma: no cover
    from collections.abc import Mapping
    from typing import Iterable

# Default EMMO version
EMMO_VERSION = "1.0.0"

# Cached module variables
_emmo_ts = None  # EMMO triplestore object
_emmo_ns = None  # EMMO namespace object
_unit_cache = {}  # Maps unit names to IRIs

# Named tuple used to represent a
#Unit = namedtuple(
#    "Unit",
#    "symbol, aliases, multiplier, offset, dimension, ucum_code, "
#    "emmo_iri, qudt_iri, om_iri"
#)


class MissingUnitError(ValueError):
    "Unit not found in ontology."


def get_emmo_triplestore(emmo_version: str = EMMO_VERSION) -> Triplestore:
    """Return, potentially cached, triplestore object containing the
    given version of EMMO."""
    global _emmo_ts
    if not _emmo_ts:
        _emmo_ts = Triplestore("rdflib")

        cachefile = get_cachedir() / f"emmo-{emmo_version}.ntriples"
        if cachefile.exists():
            _emmo_ts.parse(cachefile, format="ntriples")
        else:
            _emmo_ts.parse(f"https://w3id.org/emmo/{emmo_version}")
            _emmo_ts.serialize(cachefile, format="ntriples", encoding="utf-8")
    return _emmo_ts


def get_emmo_namespace(emmo_version: str = EMMO_VERSION) -> Namespace:
    """Return potentially cached EMMO namespace object."""
    global _emmo_ns
    if not _emmo_ns:
        _emmo_ns = Namespace(
            iri="https://w3id.org/emmo#",
            label_annotations=True,
            check=True,
            triplestore=get_emmo_triplestore(emmo_version),
        )
    return _emmo_ns


def get_unit_symbol(iri: str, emmo_version: str = EMMO_VERSION) -> str:
    """Return the unit symbol for unit with the given IRI."""
    ts = get_emmo_triplestore(emmo_version)
    EMMO = get_emmo_namespace(emmo_version)
    symbol = ts.value(iri, EMMO.unitSymbol)
    if symbol:
        return str(symbol)
    for r in ts.restrictions(iri, EMMO.unitSymbolValue, type="value"):
        symbol = r["value"]
        if symbol:
            return str(symbol)
    raise KBError("No symbol value is defined for unit:", iri)


def get_unit_iri(unit: str, emmo_version: str = EMMO_VERSION) -> str:
    """Returns the IRI for the given unit."""
    if not _unit_cache:
        ts = get_emmo_triplestore(emmo_version)
        EMMO = get_emmo_namespace(emmo_version)
        for predicate in (
            EMMO.unitSymbol,
            EMMO.ucumCode,
            EMMO.uneceCommonCode,
        ):
            for s, _, o in ts.triples(predicate=predicate):
                if o.value in _unit_cache and predicate == EMMO.unitSymbol:
                    warnings.warn(
                        f"more than one unit with symbol '{o.value}': "
                        f"{_unit_cache[o.value]}"
                    )
                else:
                    _unit_cache[o.value] = s
                for o in ts.objects(s, SKOS.prefLabel):
                    _unit_cache[o.value] = s
                for o in ts.objects(s, SKOS.altLabel):
                    if o.value not in _unit_cache:
                        _unit_cache[o.value] = s

        for r, _, o in ts.triples(predicate=OWL.hasValue):
            if ts.has(r, RDF.type, OWL.Restriction) and ts.has(
                r, OWL.onProperty, EMMO.unitSymbolValue
            ):
                s = ts.value(predicate=RDFS.subClassOf, object=r)
                _unit_cache[o.value] = s

    if unit in _unit_cache:
        return _unit_cache[unit]

    raise MissingUnitError(unit)


class Units:
    """A class representing all units in an EMMO-based ontology."""

    def __init__(
        self,
        ts: Triplestore = None,
        unit_ontology: str = "emmo",
        ontology_version: str = EMMO_VERSION,
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
            triplestore=self.ts
        )

        self.units = self._emmo_unit_iris()

    def _emmo_unit_iris(self) -> list:
        """Return a list with the IRIs of all EMMO units."""
        query = f"""
        PREFIX rdfs: <{RDFS}>
        SELECT ?unit
        WHERE {{
          ?unit rdfs:subClassOf+ ?dimunit .
          ?dimunit rdfs:subClassOf ?r .
          ?r owl:onProperty <{EMMO.hasDimensionString}> .
          FILTER NOT EXISTS {{
            ?unit rdfs:subClassOf <{EMMO.PrefixedUnit}> .
          }}
        }}
        """
        return [iri for iri, in self.ts.query(query)]

    def _get_unit_symbol(iri: str) -> str:
    """Return the unit symbol for unit with the given IRI."""
    symbol = self.ts.value(iri, self.ns.unitSymbol)
    if symbol:
        return str(symbol)
    for r in self.ts.restrictions(iri, self.ns.unitSymbolValue, type="value"):
        symbol = r["value"]
        if symbol:
            return str(symbol)
    raise KBError("No symbol value is defined for unit:", iri)


    def _parse_emmo_units(self) -> "Iterable[namedtuple]":
        """Parse EMMO units and return them as an iterator over named
        tuples."""
        for iri in self._emmo_unit_iris():
            d = {
                "symbol":
                "emmo_iri": iri,
            }
