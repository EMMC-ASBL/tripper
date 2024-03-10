"""Provides a simple representation of namespaces."""

import hashlib
import os
import pickle  # nosec
import sys
import warnings
from pathlib import Path
from typing import TYPE_CHECKING

from tripper.errors import (
    NamespaceError,
    NoSuchIRIError,
    UnusedArgumentWarning,
)

if TYPE_CHECKING:  # pragma: no cover
    from typing import Optional, Sequence, Union

    from tripper.triplestore import Triplestore


class Namespace:
    """Represent a namespace.

    Arguments:
        iri: IRI of namespace to represent.
        label_annotations: Sequence of label annotations. If given, check
            the underlying ontology during attribute access if the name
            correspond to a label. The label annotations should be ordered
            from highest to lowest precedense.
            If True is provided, `label_annotations` is set to
            ``(SKOS.prefLabel, RDF.label, SKOS.altLabel)``.
        check: Whether to check underlying ontology if the IRI exists during
            attribute access.  If true, NoSuchIRIError will be raised if the
            IRI does not exist in this namespace.
        reload: Whether to reload the ontology (which is needed when
            `label_annotations` or `check` are given) disregardless whether it
            has been cached locally.
        triplestore: Use this triplestore for label lookup and checking.
            Can be either a Triplestore object or an URL to load from.
            Defaults to `iri`.
    """

    __slots__ = (
        "_iri",  # Ontology IRI
        "_label_annotations",  # Recognised annotations for labels
        "_check",  # Whether to check that IRIs exists
        "_iris",  # Dict mapping labels to IRIs
    )

    def __init__(
        self,
        iri: str,
        label_annotations: "Sequence" = (),
        check: bool = False,
        reload: "Optional[bool]" = None,
        triplestore: "Optional[Union[Triplestore, str]]" = None,
    ):
        if label_annotations is True:
            label_annotations = (SKOS.prefLabel, RDF.label, SKOS.altLabel)

        need_triplestore = bool(check or label_annotations)

        self._iri = str(iri)
        self._label_annotations = (
            tuple(label_annotations) if label_annotations else ()
        )
        self._check = bool(check)
        self._iris: "Optional[dict]" = {} if need_triplestore else None

        if need_triplestore:
            self._update_iris(triplestore, reload=reload)

    def _update_iris(self, triplestore=None, reload=False):
        """Update the internal cache from `triplestore`.

        If `reload` is true, reload regardless we have a local cache.
        """

        # Import Triplestore here to avoid cyclic import
        from .triplestore import (  # pylint: disable=import-outside-toplevel,cyclic-import
            Triplestore,
        )

        if not reload and self._load_cache():
            return

        if triplestore is None:
            triplestore = self._iri

        if isinstance(triplestore, (str, Path)):
            # Ignore UnusedArgumentWarning when creating triplestore
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", category=UnusedArgumentWarning)
                ts = Triplestore(
                    "rdflib",
                    base_iri=self._iri,
                )
            ts.parse(triplestore)
        elif isinstance(triplestore, Triplestore):
            ts = triplestore
        elif not isinstance(triplestore, Triplestore):
            raise NamespaceError(
                "If given, `triplestore` argument must be either a URL "
                "(string), Path or a Triplestore object."
            )

        # Add (label, full_iri) pairs
        for label in reversed(self._label_annotations):
            self._iris.update(
                (getattr(o, "value", o), s)
                for s, o in ts.subject_objects(label)
                if s.startswith(self._iri)
            )

        # Add (name, full_iri) pairs
        self._iris.update(
            (s[len(self._iri) :], s)
            for s in ts.subjects()
            if s.startswith(self._iri)
        )

    def _get_cachefile(self) -> "Path":
        """Return path to cache file for this namespace."""
        name = self._iri.rstrip("#/").rsplit("/", 1)[-1]
        hashno = hashlib.shake_128(self._iri.encode()).hexdigest(5)
        return get_cachedir() / f"{name}-{hashno}.cache"

    def _save_cache(self):
        """Save current cache."""
        # pylint: disable=invalid-name
        cachefile = self._get_cachefile()
        if self._iris:
            with open(cachefile, "wb") as f:
                pickle.dump(self._iris, f)

    def _load_cache(self) -> bool:
        """Update cache with cache file.

        Returns true if there exists a cache file to load from.
        """
        # pylint: disable=invalid-name
        cachefile = self._get_cachefile()
        if self._iris is None:
            self._iris = {}
        if cachefile.exists():
            with open(cachefile, "rb") as f:
                self._iris.update(pickle.load(f))  # nosec
            return True
        return False

    def __getattr__(self, name):
        if self._iris and name in self._iris:
            return self._iris[name]
        if self._check:
            raise NoSuchIRIError(self._iri + name)
        return self._iri + name

    def __getitem__(self, key):
        return self.__getattr__(key)

    def __repr__(self):
        return f"Namespace({self._iri})"

    def __str__(self):
        return self._iri

    def __add__(self, other):
        return self._iri + str(other)

    def __hash__(self):
        return hash(self._iri)

    def __eq__(self, other):
        return self._iri == str(other)

    def __del__(self):
        if self._iris:
            self._save_cache()


def get_cachedir(create=True) -> Path:
    """Returns cross-platform path to tripper cache directory.

    If `create` is true, create the cache directory if it doesn't exists.

    The XDG_CACHE_HOME environment variable is used if it exists.
    """
    site_cachedir = os.getenv("XDG_CACHE_HOME")
    finaldir = None
    if not site_cachedir:
        if sys.platform.startswith("win32"):
            site_cachedir = Path.home() / "AppData" / "Local"
            finaldir = "Cache"
        elif sys.platform.startswith("darwin"):
            site_cachedir = Path.home() / "Library" / "Caches"
        else:  # Default to UNIX
            site_cachedir = Path.home() / ".cache"  # type: ignore
    cachedir = Path(site_cachedir) / "tripper"  # type: ignore
    if finaldir:
        cachedir /= finaldir

    if create:
        path = Path(cachedir.root)
        for part in cachedir.parts[1:]:
            path /= part
            if not path.exists():
                path.mkdir()

    return cachedir


# Pre-defined namespaces
XML = Namespace("http://www.w3.org/XML/1998/namespace")
RDF = Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#")
RDFS = Namespace("http://www.w3.org/2000/01/rdf-schema#")
XSD = Namespace("http://www.w3.org/2001/XMLSchema#")
OWL = Namespace("http://www.w3.org/2002/07/owl#")
SKOS = Namespace("http://www.w3.org/2004/02/skos/core#")
DC = Namespace("http://purl.org/dc/elements/1.1/")
DCTERMS = Namespace("http://purl.org/dc/terms/")
FOAF = Namespace("http://xmlns.com/foaf/0.1/")
DOAP = Namespace("http://usefulinc.com/ns/doap#")
PROV = Namespace("http://www.w3.org/ns/prov#")
DCAT = Namespace("http://www.w3.org/ns/dcat#")
TIME = Namespace("http://www.w3.org/2006/time#")
FNO = Namespace("https://w3id.org/function/ontology#")

# EMMO = Namespace("http://w3id.org/emmo#")
# MAP = Namespace("http://w3id.org/domain-mappings#")
# DM = Namespace("http://w3id.org/datamodel#")
# OTEIO = Namespace("http://w3id.org/oteio#")
EMMO = Namespace("http://emmo.info/emmo#")
MAP = Namespace("http://emmo.info/domain-mappings#")
DM = Namespace("http://emmo.info/datamodel#")
OTEIO = Namespace("http://emmo.info/oteio#")
