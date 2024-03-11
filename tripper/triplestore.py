"""A module encapsulating different triplestores using the strategy design
pattern.

See
https://raw.githubusercontent.com/EMMC-ASBL/tripper/master/README.md
for an introduction and for a table over available backends.

This module has no dependencies outside the standard library, but the
triplestore backends may have.

For developers: The usage of `s`, `p`, and `o` represent the different parts of
an RDF Triple: subject, predicate, and object.
"""

# pylint: disable=invalid-name,too-many-public-methods,too-many-lines
from __future__ import annotations  # Support Python 3.7 (PEP 585)

import importlib
import inspect
import re
import subprocess  # nosec
import sys
import warnings
from collections.abc import Sequence
from typing import TYPE_CHECKING

from tripper.errors import (
    CannotGetFunctionError,
    NamespaceError,
    TriplestoreError,
    UniquenessError,
)
from tripper.literal import Literal
from tripper.namespace import (
    DCTERMS,
    DM,
    EMMO,
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
from tripper.utils import en, function_id, infer_iri, split_iri

if TYPE_CHECKING:  # pragma: no cover
    from collections.abc import Mapping
    from typing import (
        Any,
        Callable,
        Dict,
        Generator,
        List,
        Optional,
        Tuple,
        Union,
    )

    from tripper.mappings import Value
    from tripper.utils import OptionalTriple, Triple

try:
    from importlib.metadata import entry_points
except ImportError:
    # Use importlib_metadata backport for Python 3.6 and 3.7
    from importlib_metadata import entry_points


# Default packages in which to look for tripper backends
backend_packages = ["tripper.backends"]


# FIXME - add the following classes and properties to ontologies
# These would be good to have in EMMO
DataSource = EMMO.DataSource
hasAccessFunction = EMMO.hasAccessFunction
hasDataValue = RDF.value  # ??
hasUnit = DM.hasUnit
hasCost = DM.hasCost


# Regular expression matching a prefixed IRI
_MATCH_PREFIXED_IRI = re.compile(r"^([a-z]+):([^/]{1}.*)$")


class Triplestore:
    """Provides a common frontend to a range of triplestore backends."""

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
        # "fno": FNO,
        # "emmo": EMMO,
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

        Parameters:
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

        """
        backend_name = backend.rsplit(".", 1)[-1]
        module = self._load_backend(backend, package)
        cls = getattr(module, f"{backend_name.title()}Strategy")
        self.base_iri = base_iri
        self.namespaces: "Dict[str, Namespace]" = {}
        self.closed = False
        self.backend_name = backend_name
        self.backend = cls(base_iri=base_iri, database=database, **kwargs)

        # Cache functions in the triplestore for fast access
        self.function_repo: "Dict[str, Union[float, Callable, None]]" = {}

        for prefix, namespace in self.default_namespaces.items():
            self.bind(prefix, namespace)

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
        if sys.version_info < (3, 10):
            # Fallback for Python < 3.10
            eps = entry_points().get("tripper.backends", ())
        else:
            # New entry_point interface from Python 3.10+
            eps = entry_points(  # pylint: disable=unexpected-keyword-arg
                group="tripper.backends"
            )
        for entry_point in eps:
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

    def add_triples(
        self, triples: "Union[Sequence[Triple], Generator[Triple, None, None]]"
    ):
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
    def close(self):
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

        Parameters:
            source: File-like object or file name.
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

        Parameters:
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

    def query(self, query_object, **kwargs) -> "List[Tuple[str, ...]]":
        """SPARQL query.

        Parameters:
            query_object: String with the SPARQL query.
            kwargs: Keyword arguments passed to the backend query() method.

        Returns:
            List of tuples of IRIs for each matching row.

        Note:
            This method is intended for SELECT queries. Use
            the update() method for INSERT and DELETE queries.

        """
        self._check_method("query")
        return self.backend.query(query_object=query_object, **kwargs)

    def update(self, update_object, **kwargs) -> None:
        """Update triplestore with SPARQL.

        Parameters:
            update_object: String with the SPARQL query.
            kwargs: Keyword arguments passed to the backend update() method.

        Note:
            This method is intended for INSERT and DELETE queries. Use
            the query() method for SELECT queries.

        """
        self._check_method("update")
        return self.backend.update(update_object=update_object, **kwargs)

    def bind(
        self, prefix: str, namespace: "Union[str, Namespace]", **kwargs
    ) -> Namespace:
        """Bind prefix to namespace and return the new Namespace object.

        The new Namespace is created with `namespace` as IRI.
        Keyword arguments are passed to the Namespace() constructor.

        If `namespace` is None, the corresponding prefix is removed.
        """
        if hasattr(self.backend, "bind"):
            self.backend.bind(prefix, namespace)

        if namespace is None:
            del self.namespaces[prefix]
            return None

        self.namespaces[prefix] = (
            namespace
            if isinstance(namespace, Namespace)
            else Namespace(namespace, **kwargs)
        )
        return self.namespaces[prefix]

    @classmethod
    def create_database(cls, backend: str, database: str, **kwargs):
        """Create a new database in backend.

        Parameters:
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

        Parameters:
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

        Parameters:
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

    @classmethod
    def _get_backend(cls, backend: str, package: "Optional[str]" = None):
        """Returns the class implementing the given backend."""
        module = cls._load_backend(backend, package=package)
        return getattr(module, f"{backend.title()}Strategy")

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

        Parameters:
            subject, predicate, object: Criteria to match. Two of these must
                be provided.
            default: Value to return if no matches are found.
            any: If true, return any matching value, otherwise raise
                UniquenessError.
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
            first = None
            if idx != 2:
                raise ValueError("`object` must be None if `lang` is given")
            for triple in triples:
                value = triple[idx]
                if isinstance(value, Literal) and value.lang == lang:
                    if any:
                        return value
                    if first:
                        raise UniquenessError("More than one match")
                    first = value
            if first is None:
                return default
        else:
            try:
                triple = next(triples)
            except StopIteration:
                return default

        try:
            next(triples)
        except StopIteration:
            return triple[idx]

        if any:
            return triple[idx]
        raise UniquenessError("More than one match")

    def subjects(
        self, predicate=None, object=None  # pylint: disable=redefined-builtin
    ):
        """Returns a generator of subjects for given predicate and object."""
        for s, _, _ in self.triples(predicate=predicate, object=object):
            yield s

    def predicates(
        self, subject=None, object=None  # pylint: disable=redefined-builtin
    ):
        """Returns a generator of predicates for given subject and object."""
        for _, p, _ in self.triples(subject=subject, object=object):
            yield p

    def objects(self, subject=None, predicate=None):
        """Returns a generator of objects for given subject and predicate."""
        for _, _, o in self.triples(subject=subject, predicate=predicate):
            yield o

    def subject_predicates(
        self, object=None
    ):  # pylint: disable=redefined-builtin
        """Returns a generator of (subject, predicate) tuples for given
        object."""
        for s, p, _ in self.triples(object=object):
            yield s, p

    def subject_objects(self, predicate=None):
        """Returns a generator of (subject, object) tuples for given
        predicate."""
        for s, _, o in self.triples(predicate=predicate):
            yield s, o

    def predicate_objects(self, subject=None):
        """Returns a generator of (predicate, object) tuples for given
        subject."""
        for _, p, o in self.triples(subject=subject):
            yield p, o

    def set(self, triple):
        """Convenience method to update the value of object.

        Removes any existing triples for subject and predicate before adding
        the given `triple`.
        """
        s, p, _ = triple
        self.remove(s, p)
        self.add(triple)

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

    # Methods providing additional functionality
    # ------------------------------------------
    def expand_iri(self, iri: str):
        """Return the full IRI if `iri` is prefixed.  Otherwise `iri` is
        returned."""
        match = re.match(_MATCH_PREFIXED_IRI, iri)
        if match:
            prefix, name = match.groups()
            if prefix not in self.namespaces:
                raise NamespaceError(f"unknown namespace: {prefix}")
            return f"{self.namespaces[prefix]}{name}"
        return iri

    def prefix_iri(self, iri: str, require_prefixed: bool = False):
        """Return prefixed IRI.

        This is the reverse of expand_iri().

        If `require_prefixed` is true, a NamespaceError exception is raised
        if no prefix can be found.
        """
        if not re.match(_MATCH_PREFIXED_IRI, iri):
            for prefix, namespace in self.namespaces.items():
                if iri.startswith(str(namespace)):
                    return f"{prefix}:{iri[len(str(namespace)):]}"
            if require_prefixed:
                raise NamespaceError(f"No prefix defined for IRI: {iri}")
        return iri

    def map(
        self,
        source: str,
        target: str,
        cost: "Optional[Union[float, Callable]]" = None,
        target_cost: bool = True,
    ):
        """Add 'mapsTo' relation to the triplestore.

        Parameters:
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

        Parameters:
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
            raise TriplestoreError(
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

        Parameters:
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

        Parameters:
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

        Parameters:
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

        Parameters:
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
        DataSet = EMMO.EMMO_194e367c_9783_4bf5_96d0_9ad597d48d9a
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
            self.add((iri, RDF.type, DataSet))
            self.add((iri, RDFS.label, en(parname)))
            self.add((func_iri, hasInput, iri))
        for iri in returns:
            self.add((iri, RDF.type, DataSet))
            self.add((func_iri, hasOutput, iri))
        if doc_string:
            self.add((func_iri, DCTERMS.description, en(doc_string)))

        return func_iri
