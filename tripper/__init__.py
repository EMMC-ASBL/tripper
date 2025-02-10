"""A package encapsulating different triplestores using the strategy design
pattern.

See the README.md file for a description for how to use this package.
"""

# Import backends here to avoid defining new globals later
# Needed for pytest+doctest to pass
from . import backends  # pylint: disable=unused-import
from .literal import Literal
from .namespace import (
    DC,
    DCAT,
    DCTERMS,
    DM,
    DOAP,
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
from .triplestore_extend import Tripper

__version__ = "0.4.0"

# Pre-defined namespaces
EMMO = Namespace(
    iri="https://w3id.org/emmo#",
    label_annotations=True,
    check=True,
)
CHAMEO = Namespace(
    iri="https://w3id.org/emmo/domain/characterisation-methodology/chameo#",
    label_annotations=True,
    check=True,
)

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
