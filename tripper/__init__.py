"""A package encapsulating different triplestores using the strategy design
pattern.

See the README.md file for a description for how to use this package.
"""

# Import backends here to avoid defining new globals later
# Needed for pytest+doctest to pass
from . import backends  # pylint: disable=unused-import
from .literal import Literal
from .namespace import (
    ADMS,
    DC,
    DCAT,
    DCATAP,
    DCTERMS,
    DM,
    DOAP,
    ELI,
    EURIO,
    FNO,
    FOAF,
    IANA,
    MAP,
    ODRL,
    OTEIO,
    OWL,
    RDF,
    RDFS,
    SCHEMA,
    SKOS,
    SPDX,
    TIME,
    VCARD,
    XML,
    XSD,
    Namespace,
)
from .session import Session
from .triplestore import Triplestore, backend_packages
from .triplestore_extend import Tripper

__version__ = "0.4.2"

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
    # Namespaces
    "ADMS",  # Asset Description Metadata Schema
    "CHAMEO",  # Characterisation Methodology Domain Ontology
    "DC",  #  Dublin Core
    "DCAT",  # Data Catalog Vocabulary
    "DCATAP",  # DCAT Application Profile
    "DCTERMS",  # Dublin Core terms
    "DM",  # Datamodel ontology
    "DOAP",  # Description of a Project
    "ELI",  # European Legislation Identifier
    "EMMO",  # Elementary Multiperspective Material Ontology
    "EURIO",  # EUropean Research Information Ontology
    "FNO",  # Function Ontology
    "FOAF",  # Friend of a Friend
    "IANA",  # IANA, registered media types
    "MAP",  # Mapping Ontology
    "ODRL",  # Open Digital Rights Language
    "OTEIO",  # Open Translation Environment Interface Ontology
    "OWL",  # Web Ontology Language
    "RDF",  # Resource Description Framework
    "RDFS",  # RDF Schema
    "SCHEMA",  # schema.org
    "SKOS",  # Simple Knowledge Organization System
    "SPDX",  # open standard for material information
    "TIME",  # Time Ontology
    "VCARD",  # vCard Ontology - for describing People and Organizations
    "XML",  # XML namespace
    "XSD",  # XML Schema Datatypes
    # Classes
    "Literal",
    "Namespace",
    "Session",
    "Triplestore",
    "Tripper",
    # Functions
    "backend_packages",
    # Other
    "__version__",
)
