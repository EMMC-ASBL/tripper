"""A module encapsulating different triplestores using the strategy
design pattern.

For a list over available backends, see
https://emmc-asbl.github.io/tripper/latest/#available-backends

This module has no dependencies outside the standard library, but
the triplestore backends may have.

For developers: The usage of `s`, `p`, and `o` represent the different
parts of an RDF Triple: subject, predicate, and object.


"""

# pylint: disable=invalid-name,too-many-public-methods,too-many-lines
from __future__ import annotations  # Support Python 3.7 (PEP 585)

import importlib
import inspect
import subprocess  # nosec
import sys
import warnings
from collections.abc import Sequence
from typing import TYPE_CHECKING

from tripper.errors import (
    ArgumentTypeError,
    ArgumentValueError,
    CannotGetFunctionError,
    TripperError,
    UniquenessError,
)
from tripper.literal import Literal
from tripper.namespace import (
    DCTERMS,
    DM,
    FNO,
    MAP,
    OTEIO,
    OWL,
    RDF,
    RDFS,
    XML,
    XSD,
    Namespace,
)
from tripper.utils import (
    bnode_iri,
    en,
    expand_iri,
    function_id,
    get_entry_points,
    infer_iri,
    prefix_iri,
    split_iri,
)

if TYPE_CHECKING:  # pragma: no cover
    from typing import (
        Any,
        Callable,
        Dict,
        Generator,
        Iterable,
        List,
        Mapping,
        Optional,
        Tuple,
        Union,
    )

    # Ideally `RestrictionType` should be defined as
    #
    #     RestrictionType = typing.Literal[
    #         "some", "only", "exactly", "min", "max", "value",
    #     ]
    #
    # but mypy doesn't like that. Also, typing.Literal was added in
    # Python 3.8 and updated in 3.9.1.  For earlier versions, there
    # exists typing_extensions, which adds to the version-dependencies
    # as well as adding an extra requirement.
    # For now we do it simple.
    RestrictionType = str

    from tripper.mappings import Value
    from tripper.utils import OptionalTriple, Triple


# Default packages in which to look for tripper backends
backend_packages = ["tripper.backends"]


# EMMO namespace with no checking and label lookup
EMMO = Namespace("https://w3id.org/emmo#")

# FIXME - add the following classes and properties to ontologies
# These would be good to have in EMMO
DataSource = EMMO.DataSource
hasAccessFunction = EMMO.hasAccessFunction
hasDataValue = RDF.value  # ??
hasUnit = DM.hasUnit
hasCost = DM.hasCost


# Regular expression matching a prefixed IRI
# _MATCH_PREFIXED_IRI = re.compile(r"^([a-z][a-z0-9]*)?:([^/]{1}.*)$")


class Triplestore:
    """Provides a common frontend to a range of triplestore backends."""

    # pylint: disable=too-many-instance-attributes

    default_namespaces = {
        "xml": XML,
        "rdf": RDF,
        "rdfs": RDFS,
        "xsd": XSD,
        "owl": OWL,
        # "skos": SKOS,
        # "dcat": DCAT,
        # "dc": DC,
        # "dcterms": DCTERMS,
        # "foaf": FOAF,
        # "doap": DOAP,
        # "map": MAP,
        # "dm": DM,
    }

    def __init__(
        self,
        backend: str,
        base_iri: "Optional[str]" = None,
        database: "Optional[str]" = None,
        package: "Optional[str]" = None,
        **kwargs,
    ) -> None:
        """Initialise triplestore using the backend with the given name.

        Arguments:
            backend: Name of the backend module.

                For built-in backends or backends provided via a
                backend package (using entrypoints), this should just
                be the name of the backend with no dots (ex: "rdflib").

                For a custom backend, you can provide the full module name,
                including the dots (ex:"mypackage.mybackend").  If `package`
                is given, `backend` is interpreted relative to `package`
                (ex: ..mybackend).

                For a list over available backends, see
                https://github.com/EMMC-ASBL/tripper#available-backends

            base_iri: Base IRI used by the add_function() method when adding
                new triples. May also be used by the backend.
            database: Name of database to connect to (for backends that
                supports it).
            package: Required when `backend` is a relative module.  In that
                case, it is relative to `package`.
            kwargs: Keyword arguments passed to the backend's __init__()
                method.

        Attributes:
            backend_name: Name of backend.
            base_iri: Assigned to the `base_iri` argument.
            closed: Whether the triplestore is closed.
            kwargs: Dict with additional keyword arguments.
            namespaces: Dict mapping namespace prefixes to IRIs.
            package: Name of Python package if the backend is implemented as
                a relative module. Assigned to the `package` argument.

        Notes:
            If the backend establishes a connection that should be closed
            it is useful to instantiate the Triplestore as a context manager:

                >>> import tripper
                >>> with tripper.Triplestore("rdflib") as ts:
                ...     print(ts.backend_name)
                rdflib

            This ensures that the connection is automatically closed when the
            context manager exits.
        """
        backend_name = backend.rsplit(".", 1)[-1]
        module = self._load_backend(backend, package)
        cls = getattr(module, f"{backend_name.title()}Strategy")
        self.base_iri = base_iri
        self.namespaces: "Dict[str, Namespace]" = {}
        self.closed = False
        self.backend_name = backend_name
        self.database = database
        self.package = package
        self.kwargs = kwargs.copy()
        self.backend = cls(base_iri=base_iri, database=database, **kwargs)

        # Cache functions in the triplestore for fast access
        self.function_repo: "Dict[str, Union[float, Callable, None]]" = {}

        for prefix, namespace in self.default_namespaces.items():
            self.bind(prefix, namespace)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    @classmethod
    def _load_backend(cls, backend: str, package: "Optional[str]" = None):
        """Load and return backend module.  The arguments has the same meaning
        as corresponding arguments to __init__().

        If `backend` contains a dot or `package` is given, import `backend`
        using `package` for relative imports.

        Otherwise, if there in the "tripper.backends" entry point group exists
        an entry point who's name matches `backend`, then the corresponding
        module is loaded.

        Otherwise, look for the `backend` in any of the (sub)packages listed
        `backend_packages` module variable.
        """
        # Explicitly specified backend
        if "." in backend or package:
            return importlib.import_module(backend, package)

        # Installed backend package
        for entry_point in get_entry_points("tripper.backends"):
            if entry_point.name == backend:
                return importlib.import_module(entry_point.module)

        # Backend module
        for pack in backend_packages:
            try:
                return importlib.import_module(f"{pack}.{backend}")
            except ModuleNotFoundError:
                pass

        raise ModuleNotFoundError(
            f"No tripper backend named '{backend}'",
            name=backend,
        )

    # Methods implemented by backend
    # ------------------------------
    def triples(  # pylint: disable=redefined-builtin
        self,
        subject: "Optional[Union[str, Triple]]" = None,
        predicate: "Optional[str]" = None,
        object: "Optional[Union[str, Literal]]" = None,
        triple: "Optional[Triple]" = None,
    ) -> "Generator[Triple, None, None]":
        """Returns a generator over matching triples.

        Arguments:
            subject: If given, match triples with this subject.
            predicate: If given, match triples with this predicate.
            object: If given, match triples with this object.
            triple: Deprecated. A `(s, p, o)` tuple where `s`, `p` and `o`
                should either be None (matching anything) or an exact IRI
                to match.

        Returns:
            Generator over all matching triples.
        """
        # __TODO__: Remove these lines when deprecated
        if triple or (subject and not isinstance(subject, str)):
            warnings.warn(
                "The `triple` argument is deprecated.  Use `subject`, "
                "`predicate` and `object` arguments instead.",
                DeprecationWarning,
                stacklevel=2,
            )
        if subject and not isinstance(subject, str):
            subject, predicate, object = subject
        elif triple:
            subject, predicate, object = triple

        return self.backend.triples((subject, predicate, object))

    def add_triples(self, triples: "Iterable[Triple]") -> None:
        """Add a sequence of triples.

        Arguments:
            triples: A sequence of `(s, p, o)` tuples to add to the
                triplestore.
        """
        self.backend.add_triples(triples)

    def remove(  # pylint: disable=redefined-builtin
        self,
        subject: "Optional[Union[str, Triple]]" = None,
        predicate: "Optional[str]" = None,
        object: "Optional[Union[str, Literal]]" = None,
        triple: "Optional[Triple]" = None,
    ) -> None:
        """Remove all matching triples from the backend.

        Arguments:
            subject: If given, match triples with this subject.
                For backward compatibility `subject` may also be an
                `(s, p, o)` triple.
            predicate: If given, match triples with this predicate.
            object: If given, match triples with this object.
            triple: Deprecated. A `(s, p, o)` tuple where `s`, `p` and `o`
                should either be None (matching anything) or an exact IRI
                to match.
        """
        # __TODO__: Remove these lines when deprecated
        if triple or (subject and not isinstance(subject, str)):
            warnings.warn(
                "The `triple` argument is deprecated.  Use `subject`, "
                "`predicate` and `object` arguments instead.",
                DeprecationWarning,
                stacklevel=2,
            )
        if subject and not isinstance(subject, str):
            subject, predicate, object = subject
        elif triple:
            subject, predicate, object = triple

        return self.backend.remove((subject, predicate, object))

    # Methods optionally implemented by backend
    # -----------------------------------------
    def close(self) -> None:
        """Calls the backend close() method if it is implemented.
        Otherwise, this method has no effect.
        """
        # It should be ok to call close() regardless of whether the backend
        # implements this method or not.  Hence, don't call _check_method().
        if not self.closed and hasattr(self.backend, "close"):
            self.backend.close()
        self.closed = True

    def parse(
        self,
        source=None,
        format=None,
        fallback_backend="rdflib",
        fallback_backend_kwargs=None,
        **kwargs,  # pylint: disable=redefined-builtin
    ) -> None:
        """Parse source and add the resulting triples to triplestore.

        Arguments:
            source: File-like object. File name or URL.
            format: Needed if format can not be inferred from source.
            fallback_backend: If the current backend doesn't implement
                parse, use the `fallback_backend` instead.
            fallback_backend_kwargs: Dict with additional keyword arguments
                for initialising `fallback_backend`.
            kwargs: Keyword arguments passed to the backend.
                The rdflib backend supports e.g. `location` (absolute
                or relative URL) and `data` (string containing the
                data to be parsed) arguments.
        """
        if hasattr(self.backend, "parse"):
            self._check_method("parse")
            self.backend.parse(source=source, format=format, **kwargs)
        else:
            if fallback_backend_kwargs is None:
                fallback_backend_kwargs = {}
            ts = Triplestore(
                backend=fallback_backend, **fallback_backend_kwargs
            )
            ts.parse(source=source, format=format, **kwargs)
            self.add_triples(ts.triples())

        if hasattr(self.backend, "namespaces"):
            for prefix, namespace in self.backend.namespaces().items():
                if prefix and prefix not in self.namespaces:
                    self.namespaces[prefix] = Namespace(namespace)

    def serialize(
        self,
        destination=None,
        format="turtle",  # pylint: disable=redefined-builtin
        fallback_backend="rdflib",
        fallback_backend_kwargs=None,
        **kwargs,
    ) -> "Union[None, str]":
        """Serialise triplestore.

        Arguments:
            destination: File name or object to write to.  If None, the
                serialisation is returned.
            format: Format to serialise as.  Supported formats, depends on
                the backend.
            fallback_backend: If the current backend doesn't implement
                serialisation, use the `fallback_backend` instead.
            fallback_backend_kwargs: Dict with additional keyword arguments
                for initialising `fallback_backend`.
            kwargs: Passed to the backend serialize() method.

        Returns:
            Serialized string if `destination` is None.
        """
        if hasattr(self.backend, "parse"):
            self._check_method("serialize")
            return self.backend.serialize(
                destination=destination, format=format, **kwargs
            )

        if fallback_backend_kwargs is None:
            fallback_backend_kwargs = {}
        ts = Triplestore(backend=fallback_backend, **fallback_backend_kwargs)
        ts.add_triples(self.triples())
        for prefix, iri in self.namespaces.items():
            ts.bind(prefix, iri)
        return ts.serialize(destination=destination, format=format, **kwargs)

    def query(self, query_object, **kwargs) -> "Any":
        """SPARQL query.

        Arguments:
            query_object: String with the SPARQL query.
            kwargs: Keyword arguments passed to the backend query() method.

        Returns:
            The return type depends on type of query:
              - SELECT: list of tuples of IRIs for each matching row
              - ASK: bool
              - CONSTRUCT, DESCRIBE: generator over triples

        Note:
            This method is intended for SELECT, ASK, CONSTRUCT and
            DESCRIBE queries.  Use the update() method for INSERT and
            DELETE queries.

            Not all backends may support all types of queries.

        """
        self._check_method("query")
        return self.backend.query(query_object=query_object, **kwargs)

    def update(self, update_object, **kwargs) -> None:
        """Update triplestore with SPARQL.

        Arguments:
            update_object: String with the SPARQL query.
            kwargs: Keyword arguments passed to the backend update() method.

        Note:
            This method is intended for INSERT and DELETE queries. Use
            the query() method for SELECT, ASK, CONSTRUCT and DESCRIBE queries.

        """
        self._check_method("update")
        return self.backend.update(update_object=update_object, **kwargs)

    def bind(  # pylint: disable=inconsistent-return-statements
        self,
        prefix: str,
        namespace: "Union[str, Namespace, Triplestore, None]" = "",
        **kwargs,
    ) -> "Union[Namespace, None]":
        """Bind prefix to namespace and return the new Namespace object.

        Arguments:
            prefix: Prefix to bind the the namespace.
            namespace: Namespace to bind to.  The default is to bind to the
                `base_iri` of the current triplestore.
                If `namespace` is None, the corresponding prefix is removed.
            kwargs: Keyword arguments are passed to the Namespace()
                constructor.

        Returns:
            New Namespace object or None if namespace is removed.
        """
        if namespace == "":
            namespace = self

        if isinstance(namespace, str):
            ns = Namespace(namespace, **kwargs)
        elif isinstance(namespace, Triplestore):
            if not namespace.base_iri:
                raise ValueError(
                    f"triplestore object {namespace} has no `base_iri`"
                )
            ns = Namespace(namespace.base_iri, **kwargs)
        elif isinstance(namespace, Namespace):
            # pylint: disable=protected-access
            ns = Namespace(namespace._iri, **kwargs)
        elif namespace is None:
            del self.namespaces[prefix]
            if hasattr(self.backend, "bind"):
                self.backend.bind(prefix, None)
            return None
        else:
            raise TypeError(f"invalid `namespace` type: {type(namespace)}")

        if hasattr(self.backend, "bind"):
            self.backend.bind(
                prefix, ns._iri  # pylint: disable=protected-access
            )

        self.namespaces[prefix] = ns
        return ns

    @classmethod
    def create_database(cls, backend: str, database: str, **kwargs):
        """Create a new database in backend.

        Arguments:
            backend: Name of backend.
            database: Name of the new database.
            kwargs: Keyword arguments passed to the backend
                create_database() method.

        Note:
            This is a class method, which operates on the backend
            triplestore without connecting to it.
        """
        cls._check_backend_method(backend, "create_database")
        backend_class = cls._get_backend(backend)
        return backend_class.create_database(database=database, **kwargs)

    @classmethod
    def remove_database(cls, backend: str, database: str, **kwargs):
        """Remove a database in backend.

        Arguments:
            backend: Name of backend.
            database: Name of the database to be removed.
            kwargs: Keyword arguments passed to the backend
                remove_database() method.

        Note:
            This is a class method, which operates on the backend
            triplestore without connecting to it.
        """
        cls._check_backend_method(backend, "remove_database")
        backend_class = cls._get_backend(backend)
        return backend_class.remove_database(database=database, **kwargs)

    @classmethod
    def list_databases(cls, backend: str, **kwargs):
        """For backends that supports multiple databases, list of all
        databases.

        Arguments:
            backend: Name of backend.
            kwargs: Keyword arguments passed to the backend
                list_databases() method.

        Note:
            This is a class method, which operates on the backend
            triplestore without connecting to it.
        """
        cls._check_backend_method(backend, "list_databases")
        backend_class = cls._get_backend(backend)
        return backend_class.list_databases(**kwargs)

    # Convenient methods
    # ------------------
    # These methods are modelled after rdflib and provide some convinient
    # interfaces to the triples(), add_triples() and remove() methods
    # implemented by all backends.

    prefer_sparql = property(
        fget=lambda self: getattr(self.backend, "prefer_sparql", None),
        doc=(
            "Whether the backend prefer SPARQL over the triples() interface. "
            "Is None if not specified by the backend."
            "\n\n"
            "Even though Tripper requires that the Triplestore.triples() is "
            "implemented, Triplestore.query() must be used for some "
            "backends in specific cases (like fuseki when working on RDF "
            "lists) because of how blank nodes are treated. "
            "\n\n"
            "The purpose of this property is to let tripper "
            "automatically select the most appropriate interface depending "
            "on the current backend settings."
        ),
    )

    @classmethod
    def _check_backend_method(cls, backend: str, name: str):
        """Checks that `backend` has a method called `name`.

        Raises NotImplementedError if it hasn't.
        """
        backend_class = cls._get_backend(backend)
        if not hasattr(backend_class, name):
            raise NotImplementedError(
                f"Triplestore backend {backend!r} do not implement a "
                f'"{name}()" method.'
            )

    @classmethod
    def _get_backend(cls, backend: str, package: "Optional[str]" = None):
        """Returns the class implementing the given backend."""
        module = cls._load_backend(backend, package=package)
        return getattr(module, f"{backend.title()}Strategy")

    def _check_method(self, name):
        """Check that backend implements the given method."""
        self._check_backend_method(self.backend_name, name)

    def add(self, triple: "Triple"):
        """Add `triple` to triplestore."""
        self.add_triples([triple])

    def value(  # pylint: disable=redefined-builtin
        self,
        subject=None,
        predicate=None,
        object=None,
        default=None,
        any=False,
        lang=None,
    ) -> "Union[str, Literal]":
        """Return the value for a pair of two criteria.

        Useful if one knows that there may only be one value.
        Two of `subject`, `predicate` or `object` must be provided.

        Arguments:
            subject: Possible criteria to match.
            predicate: Possible criteria to match.
            object: Possible criteria to match.
            default: Value to return if no matches are found.
            any: Used to define how many values to return. Can be set to:
                `False` (default): return the value or raise UniquenessError
                if there is more than one matching value.
                `True`: return any matching value if there is more than one.
                `None`: return a generator over all matching values.
            lang: If provided, require that the value must be a localised
                literal with the given language code.

        Returns:
            The value of the `subject`, `predicate` or `object` that is
            None.
        """
        spo = (subject, predicate, object)
        if sum(iri is None for iri in spo) != 1:
            raise ValueError(
                "Exactly one of `subject`, `predicate` or `object` must be "
                "None."
            )

        # Index of subject-predicate-object argument that is None
        (idx,) = [i for i, v in enumerate(spo) if v is None]

        triples = self.triples(subject, predicate, object)

        if lang:
            triples = (
                t
                for t in triples
                if isinstance(t[idx], Literal)
                and t[idx].lang == lang  # type: ignore
            )

        if any is None:
            return (t[idx] for t in triples)  # type: ignore

        try:
            value = next(triples)[idx]
        except StopIteration:
            return default

        try:
            next(triples)
        except StopIteration:
            return value

        if any is True:
            return value
        raise UniquenessError(
            f"More than one match: {(subject, predicate, object)}"
        )

    def objects(self, subject=None, predicate=None):
        """Returns a generator of objects for given subject and predicate."""
        for _, _, o in self.triples(subject=subject, predicate=predicate):
            yield o

    def predicates(
        self, subject=None, object=None  # pylint: disable=redefined-builtin
    ):
        """Returns a generator of predicates for given subject and object."""
        for _, p, _ in self.triples(subject=subject, object=object):
            yield p

    def subjects(
        self, predicate=None, object=None  # pylint: disable=redefined-builtin
    ):
        """Returns a generator of subjects for given predicate and object."""
        for s, _, _ in self.triples(predicate=predicate, object=object):
            yield s

    def predicate_objects(self, subject=None):
        """Returns a generator of (predicate, object) tuples for given
        subject."""
        for _, p, o in self.triples(subject=subject):
            yield p, o

    def subject_objects(self, predicate=None):
        """Returns a generator of (subject, object) tuples for given
        predicate."""
        for s, _, o in self.triples(predicate=predicate):
            yield s, o

    def subject_predicates(
        self, object=None
    ):  # pylint: disable=redefined-builtin
        """Returns a generator of (subject, predicate) tuples for given
        object."""
        for s, p, _ in self.triples(object=object):
            yield s, p

    def has(
        self, subject=None, predicate=None, object=None
    ):  # pylint: disable=redefined-builtin
        """Returns true if the triplestore has any triple matching
        the give subject, predicate and/or object."""
        triple = self.triples(
            subject=subject, predicate=predicate, object=object
        )
        try:
            next(triple)
        except StopIteration:
            return False
        return True

    def set(self, triple):
        """Convenience method to update the value of object.

        Removes any existing triples for subject and predicate before adding
        the given `triple`.
        """
        s, p, _ = triple
        self.remove(s, p)
        self.add(triple)

    # Methods providing additional functionality
    # ------------------------------------------
    def expand_iri(self, iri: str, strict: bool = False) -> str:
        """
        Return the full IRI if `iri` is prefixed.
        Otherwise `iri` isreturned.

        Examples:

        ```python
        >>> from tripper import Triplestore
        >>> ts = Triplestore(backend="rdflib")

        # Unknown prefix raises an exception
        >>> ts.expand_iri("ex:Concept", strict=True)  # doctest: +ELLIPSIS
        Traceback (most recent call last):
        ...
        tripper.errors.NamespaceError: Undefined prefix "ex" in IRI: ex:Concept

        >>> EX = ts.bind("ex", "http://example.com#")
        >>> ts.expand_iri("ex:Concept")
        'http://example.com#Concept'

        # Returns iri if it has no prefix
        >>> ts.expand_iri("http://example.com#Concept")
        'http://example.com#Concept'

        ```

        """
        return expand_iri(iri, self.namespaces, strict=strict)

    def prefix_iri(self, iri: str, require_prefixed: bool = False):
        # pylint: disable=line-too-long
        """Return prefixed IRI.

        This is the reverse of expand_iri().

        If `require_prefixed` is true, a NamespaceError exception is raised
        if no prefix can be found.

        Examples:

        ```python
        >>> from tripper import Triplestore
        >>> ts = Triplestore(backend="rdflib")
        >>> ts.prefix_iri("http://example.com#Concept")
        'http://example.com#Concept'

        >>> ts.prefix_iri(
        ...     "http://example.com#Concept", require_prefixed=True
        ... )  # doctest: +ELLIPSIS
        Traceback (most recent call last):
        ...
        tripper.errors.NamespaceError: No prefix defined for IRI: http://example.com#Concept

        >>> EX = ts.bind("ex", "http://example.com#")
        >>> ts.prefix_iri("http://example.com#Concept")
        'ex:Concept'

        ```

        """
        return prefix_iri(iri, self.namespaces, require_prefixed)

    # Types of restrictions defined in OWL
    _restriction_types = {
        "some": (OWL.someValueFrom, None),
        "only": (OWL.allValueFrom, None),
        "exactly": (OWL.onClass, OWL.qualifiedCardinality),
        "min": (OWL.onClass, OWL.minQualifiedCardinality),
        "max": (OWL.onClass, OWL.maxQualifiedCardinality),
        "value": (OWL.hasValue, None),
    }

    def add_restriction(  # pylint: disable=redefined-builtin
        self,
        cls: str,
        property: str,
        value: "Union[str, Literal]",
        type: "RestrictionType",
        cardinality: "Optional[int]" = None,
        hashlength: int = 16,
    ) -> str:
        """Add a restriction to a class in the triplestore.

        Arguments:
            cls: IRI of class to which the restriction applies.
            property: IRI of restriction property.
            value: The IRI or literal value of the restriction target.
            type: The type of the restriction.  Should be one of:
                - some: existential restriction (value is a class IRI)
                - only: universal restriction (value is a class IRI)
                - exactly: cardinality restriction (value is a class IRI)
                - min: minimum cardinality restriction (value is a class IRI)
                - max: maximum cardinality restriction (value is a class IRI)
                - value: Value restriction (value is an IRI of an individual
                  or a literal)

            cardinality: the cardinality value for cardinality restrictions.
            hashlength: Number of bytes in the hash part of the bnode IRI.

        Returns:
            The IRI of the created blank node representing the restriction.
        """
        iri = bnode_iri(
            prefix="restriction",
            source=f"{cls} {property} {value} {type} {cardinality}",
            length=hashlength,
        )
        triples = [
            (cls, RDFS.subClassOf, iri),
            (iri, RDF.type, OWL.Restriction),
            (iri, OWL.onProperty, property),
        ]
        if type not in self._restriction_types:
            raise ArgumentValueError(
                '`type` must be one of: "some", "only", "exactly", "min", '
                '"max" or "value"'
            )
        pred, card = self._restriction_types[type]
        triples.append((iri, pred, value))
        if card:
            if not cardinality:
                raise ArgumentTypeError(
                    f"`cardinality` must be provided for type='{type}'"
                )
            triples.append(
                (
                    iri,
                    card,
                    Literal(cardinality, datatype=XSD.nonNegativeInteger),
                ),
            )
        self.add_triples(triples)
        return iri

    def restrictions(  # pylint: disable=redefined-builtin
        self,
        cls: "Optional[str]" = None,
        property: "Optional[str]" = None,
        value: "Optional[Union[str, Literal]]" = None,
        type: "Optional[RestrictionType]" = None,
        cardinality: "Optional[int]" = None,
        asdict: bool = True,
    ) -> "Generator[dict, None, None]":
        # pylint: disable=too-many-boolean-expressions
        """Returns a generator over matching restrictions.

        Arguments:
            cls: IRI of class to which the restriction applies.
            property: IRI of restriction property.
            value: The IRI or literal value of the restriction target.
            type: The type of the restriction.  Should be one of:
                - some: existential restriction (value is a class IRI)
                - only: universal restriction (value is a class IRI)
                - exactly: cardinality restriction (value is a class IRI)
                - min: minimum cardinality restriction (value is a class IRI)
                - max: maximum cardinality restriction (value is a class IRI)
                - value: Value restriction (value is an IRI of an individual
                  or a literal)

            cardinality: the cardinality value for cardinality restrictions.
            asdict: Whether to returned generator is over dicts (see
                _get_restriction_dict()). Default is to return a generator
                over blank node IRIs.

        Returns:
            A generator over matching restrictions.  See `asdict` argument
            for types iterated over.
        """
        if type is None:
            types = set(self._restriction_types.keys())
        elif type not in self._restriction_types:
            raise ArgumentValueError(
                f"Invalid `type='{type}'`, it must be one of: "
                f"{', '.join(self._restriction_types.keys())}."
            )
        else:
            types = {type} if isinstance(type, str) else set(type)

        if isinstance(value, Literal):
            types.intersection_update({"value"})
        elif isinstance(value, str):
            types.difference_update({"value"})

        if cardinality:
            types.intersection_update({"exactly", "min", "max"})
        if not types:
            raise ArgumentValueError(
                f"Inconsistent type='{type}', value='{value}' and "
                f"cardinality='{cardinality}' arguments"
            )
        pred = {self._restriction_types[t][0] for t in types}
        card = {
            self._restriction_types[t][1]
            for t in types
            if self._restriction_types[t][1]
        }

        if cardinality:
            lcard = Literal(cardinality, datatype=XSD.nonNegativeInteger)

        for iri in self.subjects(predicate=OWL.onProperty, object=property):
            if (
                self.has(iri, RDF.type, OWL.Restriction)
                and (not cls or self.has(cls, RDFS.subClassOf, iri))
                and any(self.has(iri, p, value) for p in pred)
                and (
                    not card
                    or not cardinality
                    or any(self.has(iri, c, lcard) for c in card)
                )
            ):
                yield self._get_restriction_dict(iri) if asdict else iri

    def _get_restriction_dict(self, iri):
        """Return a dict describing restriction with `iri`.

        The returned dict has the following keys:
        - iri: (str) IRI of the restriction itself (blank node).
        - cls: (str) IRI of class to which the restriction applies.
        - property: (str) IRI of restriction property
        - type: (str) One of: "some", "only", "exactly", "min", "max", "value".
        - cardinality: (int) Restriction cardinality (optional).
        - value: (str|Literal) IRI or literal value of the restriction target.
        """
        dct = dict(self.predicate_objects(iri))
        if OWL.onClass in dct:
            ((t, p, c),) = [
                (t, p, c)
                for t, (p, c) in self._restriction_types.items()
                if c in dct
            ]
        else:
            ((t, p, c),) = [
                (t, p, c)
                for t, (p, c) in self._restriction_types.items()
                if p in dct
            ]
        return {
            "iri": iri,
            "cls": self.value(predicate=RDFS.subClassOf, object=iri),
            "property": dct[OWL.onProperty],
            "type": t,
            "cardinality": int(dct[c]) if c else None,
            "value": dct[p],
        }

    def map(
        self,
        source: str,
        target: str,
        cost: "Optional[Union[float, Callable]]" = None,
        target_cost: bool = True,
    ):
        """Add 'mapsTo' relation to the triplestore.

        Arguments:
            source: Source IRI.
            target: IRI of target ontological concept.
            cost: User-defined cost of following this mapping relation
                represented as a float.  It may be given either as a
                float or as a callable taking three arguments

                    cost(triplestore, input_iris, output_iri)

                and returning the cost as a float.
            target_cost: Whether the cost is assigned to mapping steps
                that have `target` as output.
        """
        return self.add_mapsTo(
            target=target,
            source=source,
            cost=cost,
            target_cost=target_cost,
        )

    def add_mapsTo(
        self,
        target: str,
        source: str,
        property_name: "Optional[str]" = None,
        cost: "Optional[Union[float, Callable]]" = None,
        target_cost: bool = True,
    ):
        """Add 'mapsTo' relation to triplestore.

        Arguments:
            target: IRI of target ontological concept.
            source: Source IRI (or entity object).
            property_name: Name of property if `source` is an entity or
                an entity IRI.
            cost: User-defined cost of following this mapping relation
                represented as a float.  It may be given either as a
                float or as a callable taking three arguments

                    cost(triplestore, input_iris, output_iri)

                and returning the cost as a float.
            target_cost: Whether the cost is assigned to mapping steps
                that have `target` as output.

        Note:
            This is equivalent to the `map()` method, but reverts the
            two first arguments and adds the `property_name` argument.
        """
        self.bind("map", MAP)

        if not property_name and not isinstance(source, str):
            raise TripperError(
                "`property_name` is required when `target` is not a string."
            )

        target = self.expand_iri(target)
        source = self.expand_iri(infer_iri(source))
        if property_name:
            self.add((f"{source}#{property_name}", MAP.mapsTo, target))
        else:
            self.add((source, MAP.mapsTo, target))
        if cost is not None:
            dest = target if target_cost else source
            self._add_cost(cost, dest)

    def _get_function(self, func_iri):
        """Returns Python function object corresponding to `func_iri`.

        Raises CannotGetFunctionError on failure.

        If the function is cached in the the `function_repo` attribute,
        it is returned directly.

        Otherwise an attempt is made to import the module implementing the
        function.  If that fails, the corresponding PyPI package is first
        installed before importing the module again.

        Finally the function is cached and returned.

        Note: Don't use call this method directly.  Use instead the
        `eval_function()` method, which will at some point will provide
        sandboxing for security.
        """
        if func_iri in self.function_repo and self.function_repo[func_iri]:
            return self.function_repo[func_iri]

        func_name = self.value(func_iri, OTEIO.hasPythonFunctionName)
        module_name = self.value(func_iri, OTEIO.hasPythonModuleName)
        package_name = self.value(func_iri, OTEIO.hasPythonPackageName)

        if not func_name or not module_name:
            raise CannotGetFunctionError(
                f"no documentation of how to access function: {func_iri}"
            )

        # Import module implementing the function
        try:
            module = importlib.import_module(module_name, package_name)
        except ModuleNotFoundError:
            # If we cannot find the module, try to install the pypi
            # package and try to import the module again
            pypi_package = self.value(func_iri, OTEIO.hasPypiPackageName)
            if not pypi_package:
                raise CannotGetFunctionError(  # pylint: disable=raise-missing-from
                    f"PyPI package not documented for function: {func_iri}"
                )

            try:
                subprocess.run(  # nosec
                    args=[
                        sys.executable,
                        "-m",
                        "pip",
                        "install",
                        pypi_package,
                    ],
                    check=True,
                )
            except subprocess.CalledProcessError as exc:
                raise CannotGetFunctionError(
                    f"failed installing PyPI package '{pypi_package}'"
                ) from exc

            try:
                module = importlib.import_module(module_name, package_name)
            except ModuleNotFoundError as exc:
                raise CannotGetFunctionError(
                    f"failed importing module '{module_name}'"
                    + f" from '{package_name}'"
                    if package_name
                    else ""
                ) from exc

        func = getattr(module, str(func_name))
        self.function_repo[func_iri] = func

        return func

    def eval_function(self, func_iri, args=(), kwargs=None) -> "Any":
        """Evaluate mapping function and return the result.

        Arguments:
            func_iri: IRI of the function to be evaluated.
            args: Sequence of positional arguments passed to the function.
            kwargs: Mapping of keyword arguments passed to the function.

        Returns:
            The return value of the function.

        Note:
            The current implementation does not protect against side
            effect or malicious code.  Be warned!
            This may be improved in the future.
        """
        func = self._get_function(func_iri)
        if not kwargs:
            kwargs = {}

        # FIXME: Add sandboxing
        result = func(*args, **kwargs)

        return result

    def add_function(
        self,
        func: "Union[Callable, str]",
        expects: "Union[str, Sequence, Mapping]" = (),
        returns: "Union[str, Sequence]" = (),
        base_iri: "Optional[str]" = None,
        standard: str = "emmo",
        cost: "Optional[Union[float, Callable]]" = None,
        func_name: "Optional[str]" = None,
        module_name: "Optional[str]" = None,
        package_name: "Optional[str]" = None,
        pypi_package_name: "Optional[str]" = None,
    ):
        # pylint: disable=too-many-branches,too-many-arguments
        """Inspect function and add triples describing it to the triplestore.

        Arguments:
            func: Function to describe.  Should either be a callable or a
                string with a unique function IRI.
            expects: Sequence of IRIs to ontological concepts corresponding
                to positional arguments of `func`.  May also be given as a
                dict mapping argument names to corresponding ontological IRIs.
            returns: IRI of return value.  May also be given as a sequence
                of IRIs, if multiple values are returned.
            base_iri: Base of the IRI representing the function in the
                knowledge base.  Defaults to the base IRI of the triplestore.
            standard: Name of ontology to use when describing the function.
                Valid values are:
                - "emmo": Elementary Multiperspective Material Ontology (EMMO)
                - "fno": Function Ontology (FnO)
            cost: User-defined cost of following this mapping relation
                represented as a float.  It may be given either as a
                float or as a callable taking three arguments

                    cost(triplestore, input_iris, output_iri)

                and returning the cost as a float.
            func_name: Function name.  Needed if `func` is given as an IRI.
            module_name: Fully qualified name of Python module implementing
                this function.  Default is to infer from `func`.
                implementing the function.
            package_name: Name of Python package implementing this function.
                Default is inferred from either the module or first part of
                `module_name`.
            pypi_package_name: Name and version of PyPI package implementing
                this mapping function (specified as in requirements.txt).
                Defaults to `package_name`.

        Returns:
            func_iri: IRI of the added function.
        """
        if isinstance(expects, str):
            expects = [expects]
        if isinstance(returns, str):
            returns = [returns]

        method = getattr(self, f"_add_function_{standard}")
        func_iri = method(func, expects, returns, base_iri)
        self.function_repo[func_iri] = func if callable(func) else None
        if cost is not None:
            self._add_cost(cost, func_iri)

        # Add standard-independent documentation of how to access the
        # mapping function
        self._add_function_doc(
            func=func if callable(func) else None,
            func_iri=func_iri,
            func_name=func_name,
            module_name=module_name,
            package_name=package_name,
            pypi_package_name=pypi_package_name,
        )

        return func_iri

    def _add_function_doc(
        self,
        func_iri: "str",
        func: "Optional[Callable]" = None,
        func_name: "Optional[str]" = None,
        module_name: "Optional[str]" = None,
        package_name: "Optional[str]" = None,
        pypi_package_name: "Optional[str]" = None,
    ):
        """Add standard-independent documentation of how to access the
        function.

        Arguments:
            func_iri: IRI of individual in the triplestore that stands for
                the function.
            func: Optional reference to the function itself.
            func_name: Function name.  Needed if `func` is given as an IRI.
            module_name: Fully qualified name of Python module implementing
                this function.  Default is to infer from `func`.
                implementing the function.
            package_name: Name of Python package implementing this function.
                Default is inferred from either the module or first part of
                `module_name`.
            pypi_package_name: Name and version of PyPI package implementing
                this mapping function (specified as in requirements.txt).
                Defaults to `package_name`.
        """
        if callable(func):
            func_name = func.__name__
            module = inspect.getmodule(func)
            if not module:
                raise TypeError(
                    f"inspect is not able to infer module from function "
                    f"'{func.__name__}'"
                )
            if not module_name:
                module_name = module.__name__
            if not package_name:
                package_name = module.__package__  # type: ignore
            if not pypi_package_name:
                pypi_package_name = package_name

        if func_name and module_name:
            self.bind("oteio", OTEIO)
            self.add(
                (
                    func_iri,
                    OTEIO.hasPythonFunctionName,
                    Literal(func_name, datatype=XSD.string),
                )
            )
            self.add(
                (
                    func_iri,
                    OTEIO.hasPythonModuleName,
                    Literal(module_name, datatype=XSD.string),
                )
            )
            if package_name:
                self.add(
                    (
                        func_iri,
                        OTEIO.hasPythonPackageName,
                        Literal(package_name, datatype=XSD.string),
                    )
                )
            if pypi_package_name:
                self.add(
                    (
                        func_iri,
                        OTEIO.hasPypiPackageName,
                        Literal(pypi_package_name, datatype=XSD.string),
                    )
                )
        else:
            warnings.warn(
                f"Function and module name for function '{func_name}' "
                "is not provided and cannot be inferred.  How to access "
                "the function will not be documented.",
                stacklevel=3,
            )

    def _add_cost(
        self,
        cost: "Union[float, Callable]",
        dest_iri,
        base_iri=None,
        pypi_package_name=None,
    ):
        """Help function that adds `cost` to destination IRI `dest_iri`.

        Arguments:
            cost: User-defined cost of following this mapping relation
                represented as a float.  It may be given either as a
                float or as a callable taking three arguments

                    cost(triplestore, input_iris, output_iri)

                and returning the cost as a float.
            dest_iri: destination iri that the cost should be associated with.
            base_iri: Base of the IRI representing the function in the
                knowledge base.  Defaults to the base IRI of the triplestore.
            pypi_package_name: Name and version of PyPI package implementing
                this cost function (specified as in requirements.txt).
        """
        if base_iri is None:
            base_iri = self.base_iri if self.base_iri else ":"

        if self.has(dest_iri, DM.hasCost):
            warnings.warn(f"A cost is already assigned to IRI: {dest_iri}")
        elif callable(cost):
            cost_iri = f"{base_iri}cost_function{function_id(cost)}"
            self.add(
                (dest_iri, DM.hasCost, Literal(cost_iri, datatype=XSD.anyURI))
            )
            self.function_repo[cost_iri] = cost
            self._add_function_doc(
                func=cost,
                func_iri=cost_iri,
                pypi_package_name=pypi_package_name,
            )
        else:
            self.add((dest_iri, DM.hasCost, Literal(cost)))

    def _get_cost(self, dest_iri, input_iris=(), output_iri=None):
        """Return evaluated cost for given destination iri."""
        v = self.value(dest_iri, DM.hasCost)

        if v.datatype and v.datatype != XSD.anyURI:
            return v.value
        cost = self._get_function(v.value)
        return cost(self, input_iris, output_iri)

    def _add_function_fno(self, func, expects, returns, base_iri):
        """Implementing add_function() for FnO."""
        # pylint: disable=too-many-locals,too-many-statements
        self.bind("fno", FNO)
        self.bind("dcterms", DCTERMS)
        self.bind("map", MAP)

        if base_iri is None:
            base_iri = self.base_iri if self.base_iri else ":"

        if callable(func):
            fid = function_id(func)  # Function id
            func_iri = f"{base_iri}{func.__name__}_{fid}"
            name = func.__name__
            doc_string = inspect.getdoc(func)
            parlist = f"_:{func.__name__}{fid}_parlist"
            outlist = f"_:{func.__name__}{fid}_outlist"
            if isinstance(expects, Sequence):
                pars = list(zip(expects, inspect.signature(func).parameters))
            else:
                pars = [
                    (expects[par], par)
                    for par in inspect.signature(func).parameters
                ]
        elif isinstance(func, str):
            func_iri = func
            name = split_iri(func)[1]
            doc_string = ""
            parlist = f"_:{func_iri}_parlist"
            outlist = f"_:{func_iri}_outlist"
            pariris = (
                expects if isinstance(expects, Sequence) else expects.values()
            )
            parnames = [split_iri(pariri)[1] for pariri in pariris]
            pars = list(zip(pariris, parnames))
        else:
            raise TypeError("`func` should be either a callable or an IRI")

        self.add((func_iri, RDF.type, FNO.Function))
        self.add((func_iri, RDFS.label, en(name)))
        self.add((func_iri, FNO.expects, parlist))
        self.add((func_iri, FNO.returns, outlist))
        if doc_string:
            self.add((func_iri, DCTERMS.description, en(doc_string)))

        lst = parlist
        for i, (iri, parname) in enumerate(pars):
            lst_next = f"{parlist}{i+2}" if i < len(pars) - 1 else RDF.nil
            par = f"{func_iri}_parameter{i+1}_{parname}"
            self.add((par, RDF.type, FNO.Parameter))
            self.add((par, RDFS.label, en(parname)))
            self.add((par, MAP.mapsTo, iri))
            self.add((lst, RDF.first, par))
            self.add((lst, RDF.rest, lst_next))
            lst = lst_next

        lst = outlist
        for i, iri in enumerate(returns):
            lst_next = f"{outlist}{i+2}" if i < len(returns) - 1 else RDF.nil
            val = f"{func_iri}_output{i+1}"
            self.add((val, RDF.type, FNO.Output))
            self.add((val, MAP.mapsTo, iri))
            self.add((lst, RDF.first, val))
            self.add((lst, RDF.rest, lst_next))
            lst = lst_next

        return func_iri

    def _add_function_emmo(self, func, expects, returns, base_iri):
        """Implementing add_function() method for the "emmo" standard."""
        # pylint: disable=too-many-locals
        self.bind("emmo", EMMO)
        self.bind("dcterms", DCTERMS)
        self.bind("map", MAP)

        # Hardcode EMMO IRIs to avoid slow lookup
        Task = EMMO.EMMO_4299e344_a321_4ef2_a744_bacfcce80afc
        Datum = EMMO.EMMO_50d6236a_7667_4883_8ae1_9bb5d190423a
        hasInput = EMMO.EMMO_36e69413_8c59_4799_946c_10b05d266e22
        hasOutput = EMMO.EMMO_c4bace1d_4db0_4cd3_87e9_18122bae2840
        # Software = EMMO.EMMO_8681074a_e225_4e38_b586_e85b0f43ce38
        # hasSoftware = EMMO.Software  # TODO: fix when EMMO has hasSoftware

        if base_iri is None:
            base_iri = self.base_iri if self.base_iri else ":"

        if callable(func):
            fid = function_id(func)  # Function id
            func_iri = f"{base_iri}{func.__name__}_{fid}"
            name = func.__name__
            doc_string = inspect.getdoc(func)
            if isinstance(expects, Sequence):
                pars = list(zip(inspect.signature(func).parameters, expects))
            else:
                pars = expects.items()
        elif isinstance(func, str):
            func_iri = func
            name = split_iri(func)[1]
            doc_string = ""
            pariris = (
                expects if isinstance(expects, Sequence) else expects.values()
            )
            parnames = [split_iri(pariri)[1] for pariri in pariris]
            pars = list(zip(parnames, pariris))
        else:
            raise TypeError("`func` should be either a callable or an IRI")

        self.add((func_iri, RDF.type, Task))
        self.add((func_iri, RDFS.label, en(name)))
        for parname, iri in pars:
            self.add((iri, RDF.type, Datum))
            self.add((iri, RDFS.label, en(parname)))
            self.add((func_iri, hasInput, iri))
        for iri in returns:
            self.add((iri, RDF.type, Datum))
            self.add((func_iri, hasOutput, iri))
        if doc_string:
            self.add((func_iri, DCTERMS.description, en(doc_string)))

        return func_iri
