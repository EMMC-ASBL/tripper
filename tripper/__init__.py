"""A package encapsulating different triplestores using the strategy design
pattern.

See the README.md file for a description for how to use this package.
"""
from .errors import NamespaceError, NoSuchIRIError, TriplestoreError, UniquenessError
from .literal import Literal, en, parse_literal
from .namespace import (
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
    Namespace,
)
from .triplestore import Triplestore, split_iri

__version__ = "0.1.1"

__all__ = (
    "NamespaceError",
    "NoSuchIRIError",
    "TriplestoreError",
    "UniquenessError",
    #
    "Literal",
    "en",
    "parse_literal",
    #
    "DC",
    "DCTERMS",
    "DM",
    "DOAP",
    "EMMO",
    "FNO",
    "FOAF",
    "MAP",
    "OWL",
    "RDF",
    "RDFS",
    "SKOS",
    "XML",
    "XSD",
    "Namespace",
    #
    "Triplestore",
    "split_iri",
)
