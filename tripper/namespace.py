"""Provides a simple representation of namespaces."""

import warnings

from tripper.errors import (
    NamespaceError,
    NoSuchIRIError,
    UnusedArgumentWarning,
)


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
        cachemode: Should be one of:
              - Namespace.NO_CACHE: Turn off caching.
              - Namespace.USE_CACHE: Cache attributes as they are looked up.
              - Namespace.ONLY_CACHE: Cache all names at initialisation time.
                Do not access the triplestore after that.
            Default is `NO_CACHE` if neither `label_annotations` or `check`
            is given, otherwise `USE_CACHE`.
        triplestore: Use this triplestore for label lookup and checking.
            If not given, and either `label_annotations` or `check` are
            enabled, a new rdflib triplestore will be created.
        triplestore_url: Alternative URL to use for loading the underlying
            ontology if `triplestore` is not given.  Defaults to `iri`.
    """

    NO_CACHE = 0
    USE_CACHE = 1
    ONLY_CACHE = 2

    __slots__ = (
        "_iri",
        "_label_annotations",
        "_check",
        "_cache",
        "_triplestore",
    )

    def __init__(
        self,
        iri,
        label_annotations=(),
        check=False,
        cachemode=-1,
        triplestore=None,
        triplestore_url=None,
    ):
        if label_annotations is True:
            label_annotations = (SKOS.prefLabel, RDF.label, SKOS.altLabel)

        self._iri = str(iri)
        self._label_annotations = tuple(label_annotations)
        self._check = bool(check)

        need_triplestore = bool(check or label_annotations)
        if cachemode == -1:
            cachemode = (
                Namespace.ONLY_CACHE
                if need_triplestore
                else Namespace.NO_CACHE
            )

        if need_triplestore and triplestore is None:
            # Import Triplestore here to break cyclic-import
            from .triplestore import (  # pylint: disable=import-outside-toplevel,cyclic-import
                Triplestore,
            )

            # Create triplestore, while ignoring UnusedArgumentWarning
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", category=UnusedArgumentWarning)
                triplestore = Triplestore(
                    "rdflib", base_iri=iri, triplestore_url=triplestore_url
                )

        self._cache = {} if cachemode != Namespace.NO_CACHE else None
        #
        # FIXME:
        # Change this to only assigning the triplestore if cachemode is
        # ONLY_CACHE when we figure out a good way to pre-populate the
        # cache with IRIs from the triplestore.
        #
        # self._triplestore = (
        #    triplestore if cachemode != Namespace.ONLY_CACHE else None
        # )
        self._triplestore = triplestore if need_triplestore else None

        if cachemode != Namespace.NO_CACHE:
            self._update_cache(triplestore)

    def _update_cache(self, triplestore=None):
        """Update the internal cache from `triplestore`."""
        if not triplestore:
            triplestore = self._triplestore
        if not triplestore:
            raise NamespaceError(
                "`triplestore` argument needed for updating the cache"
            )
        if self._cache is None:
            self._cache = {}

        # Add (label, full_iri) pairs to cache
        for label in reversed(self._label_annotations):
            self._cache.update(
                (o, s)
                for s, o in triplestore.subject_objects(label)
                if s.startswith(self._iri)
            )

        # Add (name, full_iri) pairs to cache
        # Currently we only check concepts that defines RDFS.isDefinedBy
        # relations.
        # Is there an efficient way to loop over all IRIs in this namespace?
        self._cache.update(
            (s[len(self._iri) :], s)
            for s in triplestore.subjects(RDFS.isDefinedBy, self._iri)
            if s.startswith(self._iri)
        )

    def __getattr__(self, name):
        if self._cache and name in self._cache:
            return self._cache[name]

        if self._triplestore:
            # Check if ``iri = self._iri + name`` is in the triplestore.
            # If so, add it to the cache.
            # We only need to check that generator returned by
            # `self._triplestore.predicate_objects(iri)` is non-empty.
            iri = self._iri + name
            predicate_object = self._triplestore.predicate_objects(iri)
            try:
                predicate_object.__next__()
            except StopIteration:
                pass
            else:
                if self._cache is not None:
                    self._cache[name] = iri
                return iri

            # Check for label annotations matching `name`.
            for label in self._label_annotations:
                for s, o in self._triplestore.subject_objects(label):
                    if o == name and s.startswith(self._iri):
                        if self._cache is not None:
                            self._cache[name] = s
                        return s

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

EMMO = Namespace("http://emmo.info/emmo#")
MAP = Namespace("http://emmo.info/domain-mappings#")
DM = Namespace("http://emmo.info/datamodel#")
OTEIO = Namespace("http://emmo.info/oteio#")
