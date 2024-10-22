"""A package encapsulating different triplestores using the strategy design
pattern.

See the README.md file for a description for how to use this package.
"""

from .literal import Literal
from .namespace import (
    CHAMEO,
    DC,
    DCAT,
    DCTERMS,
    DM,
    DOAP,
    EMMO,
    FNO,
    FOAF,
    MAP,
    OTEIO,
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

__version__ = "0.3.4"

__all__ = (
    "Literal",
    #
    "CHAMEO",
    "DCAT",
    "DC",
    "DCTERMS",
    "DM",
    "DOAP",
    "EMMO",
    "FNO",
    "FOAF",
    "MAP",
    "OTEIO",
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
