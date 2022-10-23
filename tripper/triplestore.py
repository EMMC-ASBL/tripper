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
from __future__ import annotations  # Support Python 3.7 (PEP 585)

import hashlib
import inspect
import re
import warnings
from collections.abc import Sequence
from importlib import import_module
from typing import TYPE_CHECKING

from .errors import NamespaceError, TriplestoreError, UniquenessError
from .literal import Literal, en
from .namespace import DCTERMS, DM, FNO, MAP, OWL, RDF, RDFS, XML, XSD, Namespace

if TYPE_CHECKING:  # pragma: no cover
    from collections.abc import Mapping
    from typing import Any, Callable, Dict, Generator, Tuple, Union

    Triple = Tuple[Union[str, None], Union[str, None], Union[str, None]]


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

    def __init__(self, backend: str, base_iri: str = None, **kwargs):
        """Initialise triplestore using the backend with the given name.

        Parameters:
            backend: Name of the backend module.
            base_iri: Base IRI used by the add_function() method when adding
                new triples.
            kwargs: Keyword arguments passed to the backend's __init__()
                method.
        """
        module = import_module(
            backend if "." in backend else f"tripper.backends.{backend}"
        )
        cls = getattr(module, backend.title() + "Strategy")
        self.base_iri = base_iri
        self.namespaces: "Dict[str, Namespace]" = {}
        self.backend_name = backend
        self.backend = cls(base_iri=base_iri, **kwargs)
        # Keep functions in the triplestore for convienence even though
        # they usually do not belong to the triplestore per se.
        self.function_repo: "Dict[str, Union[float, Callable[[], float]]]" = {}
        for prefix, namespace in self.default_namespaces.items():
            self.bind(prefix, namespace)

    # Methods implemented by backend
    # ------------------------------
    def triples(self, triple: "Triple") -> "Generator":
        """Returns a generator over matching triples."""
        return self.backend.triples(triple)

    def add_triples(self, triples: "Sequence[Triple]"):
        """Add a sequence of triples."""
        self.backend.add_triples(triples)

    def remove(self, triple: "Triple"):
        """Remove all matching triples from the backend."""
        self.backend.remove(triple)

    # Methods optionally implemented by backend
    # -----------------------------------------
    def parse(
        self, source=None, format=None, **kwargs  # pylint: disable=redefined-builtin
    ):
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

    def query(self, query_object, **kwargs):
        """SPARQL query."""
        self._check_method("query")
        return self.backend.query(query_object=query_object, **kwargs)

    def update(self, update_object, **kwargs):
        """Update triplestore with SPARQL."""
        self._check_method("update")
        return self.backend.update(update_object=update_object, **kwargs)

    def bind(self, prefix: str, namespace: "Union[str, Namespace]", **kwargs):
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

    # Convenient methods
    # ------------------
    # These methods are modelled after rdflib and provide some convinient
    # interfaces to the triples(), add_triples() and remove() methods
    # implemented by all backends.
    def _check_method(self, name):
        """Check that backend implements the given method."""
        if not hasattr(self.backend, name):
            raise NotImplementedError(
                f"Triplestore backend {self.backend_name!r} do not implement a "
                f'"{name}()" method.'
            )

    def add(self, triple: "Triple"):
        """Add `triple` to triplestore."""
        self.add_triples([triple])

    def value(
        self, subject=None, predicate=None, object=None, default=None, any=False
    ):  # pylint: disable=redefined-builtin
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

    def add_mapsTo(  # pylint: disable=invalid-name
        self,
        target: str,
        source: str,
        property_name: str = None,
        cost: "Union[float, Callable]" = None,
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
        base_iri: str = None,
        standard: str = "fno",
        cost: "Union[float, Callable]" = None,
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
        if callable(func):
            self.function_repo[func_iri] = func
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
            self.add((dest_iri, DM.hasCost, Literal(cost).n3()))

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
            parnames = [split_iri(par)[1] for par in pariris]
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


def function_id(func: "Callable", length: int = 4) -> str:
    """Return a checksum for function `func`.

    The returned object is a string of hexadecimal digits.

    `length` is the number of bytes in the returned checksum.  Since
    the current implementation is based on the shake_128 algorithm,
    it make no sense to set `length` larger than 32 bytes.
    """
    # return hex(crc32(inspect.getsource(func).encode())).lstrip('0x')
    return hashlib.shake_128(  # pylint: disable=too-many-function-args
        inspect.getsource(func).encode()
    ).hexdigest(length)


def infer_iri(obj):
    """Return IRI of the individual that stands for object `obj`."""
    if isinstance(obj, str):
        return obj
    if hasattr(obj, "uri") and obj.uri:
        # dlite.Metadata or dataclass (or instance with uri)
        return obj.uri
    if hasattr(obj, "uuid") and obj.uuid:
        # dlite.Instance or dataclass
        return obj.uuid
    if hasattr(obj, "schema") and callable(obj.schema):
        # pydantic.BaseModel
        schema = obj.schema()
        properties = schema["properties"]
        if "uri" in properties and properties["uri"]:
            return properties["uri"]
        if "uuid" in properties and properties["uuid"]:
            return properties["uuid"]
    raise TypeError("cannot infer IRI from object {obj!r}")


def split_iri(iri: str) -> "Tuple[str, str]":
    """Split iri into namespace and name parts and return them as a tuple."""
    if "#" in iri:
        namespace, name = iri.rsplit("#", 1)
        return f"{namespace}#", name

    if "/" in iri:
        namespace, name = iri.rsplit("/", 1)
        return f"{namespace}/", name

    raise ValueError("all IRIs should contain a slash")
