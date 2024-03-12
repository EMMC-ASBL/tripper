"""A package encapsulating different triplestores using the strategy design
pattern.

See the README.md file for a description for how to use this package.
"""

from .literal import Literal
from .namespace import (
    DC,
    DCAT,
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
from .triplestore import Triplestore, backend_packages
from .tripper import Tripper

__version__ = "0.2.15"

__all__ = (
    "Literal",
    #
    "DCAT",
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
    "backend_packages",
    "Tripper",
    #
    "__version__",
)
