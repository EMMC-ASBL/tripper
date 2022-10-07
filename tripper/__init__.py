"""A package encapsulating different triplestores using the strategy design
pattern.

See the README.md file for a description for how to use this package.
"""
from .triplestore import (
    DC,
    DCTERMS,
    DM,
    DOAP,
    EMMO,
    FNO,
    FOAF,
    MAP,
    OWL,
    RDF,
    RDFS,
    SKOS,
    XML,
    XSD,
    Literal,
    Namespace,
    Triplestore,
    en,
)

__version__ = "0.1.0"


__all__ = (
    "Literal",
    "Namespace",
    "Triplestore",
    "en",
    "XML",
    "RDF",
    "RDFS",
    "XSD",
    "OWL",
    "SKOS",
    "DC",
    "DCTERMS",
    "FOAF",
    "DOAP",
    "FNO",
    "EMMO",
    "MAP",
    "DM",
)
