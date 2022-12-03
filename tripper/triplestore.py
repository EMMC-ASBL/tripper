"""A module encapsulating different triplestores using the strategy design
pattern.

See
https://raw.githubusercontent.com/EMMC-ASBL/tripper/master/README.md
for an introduction.

This module has no dependencies outside the standard library, but the
triplestore backends may have.

For developers: The usage of `s`, `p`, and `o` represent the different parts of an
RDF Triple: subject, predicate, and object.
"""
# pylint: disable=invalid-name,too-many-public-methods
from __future__ import annotations  # Support Python 3.7 (PEP 585)

import inspect
import re
import warnings
from collections.abc import Sequence
from importlib import import_module
from typing import TYPE_CHECKING

from tripper.errors import NamespaceError, TriplestoreError, UniquenessError
from tripper.literal import Literal
from tripper.namespace import DCTERMS, DM, FNO, MAP, OWL, RDF, RDFS, XML, XSD, Namespace
from tripper.utils import en, function_id, infer_iri, split_iri

if TYPE_CHECKING:  # pragma: no cover
    from collections.abc import Mapping
    from typing import Callable, Dict, Generator, List, Optional, Tuple, Union

    from tripper.utils import OptionalTriple, Triple


# Regular expression matching a prefixed IRI
_MATCH_PREFIXED_IRI = re.compile(r"^([a-z]+):([^/]{2}.*)$")


class Triplestore:
    """Provides a common frontend to a range of triplestore backends."""

    default_namespaces = {
        "xml": XML,
        "rdf": RDF,
        "rdfs": RDFS,
        "xsd": XSD,
        "owl": OWL,
        # "skos": SKOS,
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
        **kwargs,
    ) -> None:
        """Initialise triplestore using the backend with the given name.

        Parameters:
            backend: Name of the backend module.
            base_iri: Base IRI used by the add_function() method when adding
                new triples. May also be used by the backend.
            database: Name of database to connect to (for backends that supports it).
            kwargs: Keyword arguments passed to the backend's __init__()
                method.
        """
        module = import_module(
            backend if "." in backend else f"tripper.backends.{backend}"
        )
        cls = getattr(module, f"{backend.title()}Strategy")
        self.base_iri = base_iri
        self.namespaces: "Dict[str, Namespace]" = {}
        self.closed = False
        self.backend_name = backend
        self.backend = cls(base_iri=base_iri, database=database, **kwargs)
        # Keep functions in the triplestore for convienence even though
        # they usually do not belong to the triplestore per se.
        self.function_repo: "Dict[str, Union[float, Callable[[], float], None]]" = {}
        for prefix, namespace in self.default_namespaces.items():
            self.bind(prefix, namespace)

    # Methods implemented by backend
    # ------------------------------
    def triples(self, triple: "Triple") -> "Generator[Triple, None, None]":
        """Returns a generator over matching triples.

        Arguments:
            triple: A `(s, p, o)` tuple where `s`, `p` and `o` should
                either be None (matching anything) or an exact IRI to
                match.
        """
        return self.backend.triples(triple)

    def add_triples(self, triples: "Sequence[Triple]"):
        """Add a sequence of triples.

        Arguments:
            triples: A sequence of `(s, p, o)` tuples to add to the
                triplestore.
        """
        self.backend.add_triples(triples)

    def remove(self, triple: "Triple") -> None:
        """Remove all matching triples from the backend."""
        self.backend.remove(triple)

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
        self, source=None, format=None, **kwargs  # pylint: disable=redefined-builtin
    ) -> None:
        """Parse source and add the resulting triples to triplestore.

        Parameters:
            source: File-like object or file name.
            format: Needed if format can not be inferred from source.
            kwargs: Keyword arguments passed to the backend.
                The rdflib backend supports e.g. `location` (absolute
                or relative URL) and `data` (string containing the
                data to be parsed) arguments.
        """
        self._check_method("parse")
        self.backend.parse(source=source, format=format, **kwargs)

        if hasattr(self.backend, "namespaces"):
            for prefix, namespace in self.backend.namespaces().items():
                if prefix and prefix not in self.namespaces:
                    self.namespaces[prefix] = Namespace(namespace)

    def serialize(
        self,
        destination=None,
        format="turtle",  # pylint: disable=redefined-builtin
        **kwargs,
    ) -> "Union[None, str]":
        """Serialise triplestore.

        Parameters:
            destination: File name or object to write to.  If None, the
                serialisation is returned.
            format: Format to serialise as.  Supported formats, depends on
                the backend.
            kwargs: Passed to the backend serialize() method.

        Returns:
            Serialized string if `destination` is None.
        """
        self._check_method("serialize")
        return self.backend.serialize(destination=destination, format=format, **kwargs)

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
    def _get_backend(cls, backend: str):
        """Returns the class implementing the given backend."""
        module = import_module(
            backend if "." in backend else f"tripper.backends.{backend}"
        )
        return getattr(module, f"{backend.title()}Strategy")

    @classmethod
    def _check_backend_method(cls, backend: str, name: str):
        """Checks that `backend` has a method called `name`.

        Raises NotImplementedError if it hasn't.
        """
        backend_class = cls._get_backend(backend)
        if not hasattr(backend_class, name):
            raise NotImplementedError(
                f'Triplestore backend {backend!r} do not implement a "{name}()" method.'
            )

    def _check_method(self, name):
        """Check that backend implements the given method."""
        self._check_backend_method(self.backend_name, name)

    def add(self, triple: "Triple"):
        """Add `triple` to triplestore."""
        self.add_triples([triple])

    def value(  # pylint: disable=redefined-builtin
        self, subject=None, predicate=None, object=None, default=None, any=False
    ):
        """Return the value for a pair of two criteria.

        Useful if one knows that there may only be one value.

        Parameters:
            subject, predicate, object: Triple to match.
            default: Value to return if no matches are found.
            any: If true, return any matching value, otherwise raise
                UniquenessError.
        """
        triple = self.triples((subject, predicate, object))
        try:
            value = next(triple)
        except StopIteration:
            return default

        if any:
            return value

        try:
            next(triple)
        except StopIteration:
            return value
        else:
            raise UniquenessError("More than one match")

    def subjects(
        self, predicate=None, object=None  # pylint: disable=redefined-builtin
    ):
        """Returns a generator of subjects for given predicate and object."""
        for s, _, _ in self.triples((None, predicate, object)):
            yield s

    def predicates(
        self, subject=None, object=None  # pylint: disable=redefined-builtin
    ):
        """Returns a generator of predicates for given subject and object."""
        for _, p, _ in self.triples((subject, None, object)):
            yield p

    def objects(self, subject=None, predicate=None):
        """Returns a generator of objects for given subject and predicate."""
        for _, _, o in self.triples((subject, predicate, None)):
            yield o

    def subject_predicates(self, object=None):  # pylint: disable=redefined-builtin
        """Returns a generator of (subject, predicate) tuples for given
        object."""
        for s, p, _ in self.triples((None, None, object)):
            yield s, p

    def subject_objects(self, predicate=None):
        """Returns a generator of (subject, object) tuples for given
        predicate."""
        for s, _, o in self.triples((None, predicate, None)):
            yield s, o

    def predicate_objects(self, subject=None):
        """Returns a generator of (predicate, object) tuples for given
        subject."""
        for _, p, o in self.triples((subject, None, None)):
            yield p, o

    def set(self, triple):
        """Convenience method to update the value of object.

        Removes any existing triples for subject and predicate before adding
        the given `triple`.
        """
        s, p, _ = triple
        self.remove((s, p, None))
        self.add(triple)

    def has(
        self, subject=None, predicate=None, object=None
    ):  # pylint: disable=redefined-builtin
        """Returns true if the triplestore has any triple matching
        the give subject, predicate and/or object."""
        triple = self.triples((subject, predicate, object))
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
                float or as a callable taking the value of the mapped
                quantity as input and returning the cost as a float.
            target_cost: Whether the cost is assigned to mapping steps
                that have `target` as output.
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

    def add_function(
        self,
        func: "Union[Callable, str]",
        expects: "Union[str, Sequence, Mapping]" = (),
        returns: "Union[str, Sequence]" = (),
        base_iri: "Optional[str]" = None,
        standard: str = "fno",
        cost: "Optional[Union[float, Callable]]" = None,
    ):
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
                Defaults to the Function Ontology (FnO).
            cost: User-defined cost of following this mapping relation
                represented as a float.  It may be given either as a
                float or as a callable taking the same arguments as `func`
                returning the cost as a float.

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

        return func_iri

    def _add_cost(self, cost: "Union[float, Callable[[], float]]", dest_iri):
        """Help function that adds `cost` to destination IRI `dest_iri`.

        `cost` should be either a float or a Callable returning a float.

        If `cost` is a callable it is just referred to with a literal
        id and is not ontologically described as a function.  The
        expected input arguments depends on the context, which is why
        this function is not part of the public API.  Use the add_mapsTo()
        and add_function() methods instead.
        """
        if self.has(dest_iri, DM.hasCost):
            warnings.warn(f"A cost is already assigned to IRI: {dest_iri}")
        elif callable(cost):
            cost_id = f"cost_function{function_id(cost)}"
            self.add((dest_iri, DM.hasCost, Literal(cost_id)))
            self.function_repo[cost_id] = cost
        else:
            self.add((dest_iri, DM.hasCost, Literal(cost)))

    def _add_function_fno(self, func, expects, returns, base_iri):
        """Implementing add_function() for FnO."""
        self.bind("fno", FNO)
        self.bind("dcterms", DCTERMS)
        self.bind("map", MAP)

        if base_iri is None:
            base_iri = self.base_iri if self.base_iri else ":"

        if callable(func):
            fid = function_id(func)  # Function id
            func_iri = f"{base_iri}{func.__name__}_{fid}"
            doc_string = inspect.getdoc(func)
            parlist = f"_:{func.__name__}{fid}_parlist"
            outlist = f"_:{func.__name__}{fid}_outlist"
            if isinstance(expects, Sequence):
                pars = list(zip(expects, inspect.signature(func).parameters))
            else:
                pars = [
                    (expects[par], par) for par in inspect.signature(func).parameters
                ]
        elif isinstance(func, str):
            func_iri = func
            doc_string = ""
            parlist = f"_:{func_iri}_parlist"
            outlist = f"_:{func_iri}_outlist"
            pariris = expects if isinstance(expects, Sequence) else expects.values()
            parnames = [split_iri(pariri)[1] for pariri in pariris]
            pars = list(zip(pariris, parnames))
        else:
            raise TypeError("`func` should be either a callable or an IRI")

        self.add((func_iri, RDF.type, FNO.Function))
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
