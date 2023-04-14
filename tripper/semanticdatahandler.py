from __future__ import annotations  # Support Python 3.7 (PEP 585)

import importlib
import inspect
import re
import sys
import uuid
import warnings
from collections.abc import Sequence
from typing import TYPE_CHECKING

from tripper.errors import NamespaceError, TriplestoreError, UniquenessError
from tripper.literal import Literal
from tripper.namespace import (
    DCTERMS,
    DM,
    EMMO,
    FNO,
    MAP,
    OWL,
    RDF,
    RDFS,
    XML,
    XSD,
    Namespace,
)
from tripper.utils import (
    en,
    function_id,
    infer_iri,
    parse_literal,
    random_string,
    split_iri,
)

if TYPE_CHECKING:  # pragma: no cover
    from collections.abc import Mapping
    from typing import Any, Callable, Dict, Generator, List, Optional, Tuple, Union

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
_MATCH_PREFIXED_IRI = re.compile(r"^([a-z]+):([^/]{2}.*)$")



class SematicDataHandler:
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
            base_iri: Base IRI used by the add_function() method when adding
                new triples. May also be used by the backend.
            database: Name of database to connect to (for backends that
                supports it).
            package: Required when `backend` is a relative module.  In that
                case, it is relative to `package`.
            kwargs: Keyword arguments passed to the backend's __init__()
                method.

        """
        module = self._load_backend(backend, package)
        cls = getattr(module, f"{backend.title()}Strategy")
        self.base_iri = base_iri
        self.namespaces: "Dict[str, Namespace]" = {}
        self.closed = False
        self.backend_name = backend
        self.backend = cls(base_iri=base_iri, database=database, **kwargs)

        # Keep functions in the triplestore for convienence even though
        # they usually do not belong to the triplestore per se.
        self.function_repo: "Dict[str, Union[float, Callable, None]]" = {}
        for prefix, namespace in self.default_namespaces.items():
            self.bind(prefix, namespace)

    def add_data(
        self,
        func: "Union[Callable, Literal]",
        iri: "Optional[Union[str, Sequence]]" = None,
        configurations: "Optional[dict]" = None,
        base_iri: "Optional[str]" = None,
        standard: str = "emmo",
        cost: "Optional[Union[float, Callable]]" = None,
    ) -> str:
        """Register a data source to the triplestore.

        Parameters:
            func: A callable that should return the value of the registered
                data source.  It is called with following protopype:

                    func(returns, configurations, triplestore)

                The returned value may in principle be of any type, but for
                values with unit, it is recommended to return a
                tripper.mappings.Value object.
                Alternatively, `func` may also be a literal value.
            iri: IRI of ontological concept or individual that the data
                returned by `func` should be mapped to.  If `func` is a
                callable and multiple values are returned, it may also be
                given as a sequenceof IRIs.
                If not given, it will default to a new blank node.
            configurations: Configurations passed on to `func`.
            base_iri: Base of the IRI representing the function in the
                knowledge base.  Defaults to the base IRI of the triplestore.
            standard: Name of ontological standard to use when describing the
                function.  Valid values are:
                - "emmo": Elementary Multiperspective Material Ontology (EMMO)
                - "fno": Function Ontology (FnO)
            cost: User-defined cost of following this mapping relation
                represented as a float.  It may be given either as a
                float or as a callable taking the same arguments as `func`
                returning the cost as a float.

        Returns:
            IRI of data source.
        """
        if iri is None:
            # pylint complains about uuid being unused if we make this an
            # f-string
            iri = "_bnode_" + str(uuid.uuid4())
        data_source = "_data_source_" + random_string(8)
        self.add((data_source, RDF.type, DataSource))

        if isinstance(func, Literal):
            self.add((data_source, hasDataValue, func))
            if cost is not None:
                self._add_cost(cost, data_source)
            if isinstance(iri, str):
                self.map(data_source, iri)
            else:
                raise TypeError("literal data can only have a single `iri`")

        elif callable(func):

            def fn():
                return func(iri, configurations, self)

            # Include data source IRI in documentation to ensure that the
            # function_id of `fn()` will differ for different data sources...
            fn.__doc__ = f"Function for data source: {data_source}.\n\n{func.__doc__}"
            fn.__name__ = func.__name__

            func_iri = self.add_function(
                fn,
                expects=(),
                returns=iri,
                base_iri=base_iri,
                standard=standard,
                cost=cost,
            )
            self.add((data_source, hasAccessFunction, func_iri))
        else:
            raise TypeError(f"`func` must be a callable or literal, got {type(func)}")

        return data_source

    def get_value(
        self,
        iri,
        routeno=0,
        unit: "Optional[str]" = None,
        magnitude: bool = False,
        quantity: "Optional[Any]" = None,
        **kwargs,
    ) -> "Value":
        """Return the value of an individual.

        Parameters:
            iri: IRI of individual who's value we want to return.  IRI may
                either refer to a data source or an individual mapped to
                an ontological concept.
            routeno: Number identifying the mapping route to apply for
                retrieving the individual value in case IRI does not refer
                to a data source.
            unit: return the result in the given unit.
                Implies `magnitude=True`.
            magnitude: Whether to only return the magnitude of the evaluated
                value (with no unit).
            quantity: Quantity class to use for evaluation.  Defaults to pint.
            kwargs: Additional arguments passed on to `mapping_routes()`.

        Returns:
            The value of the individual.
        """
        from tripper.mappings import (  # pylint: disable=import-outside-toplevel
            Value,
            mapping_routes,
        )

        if self.has(iri, RDF.type, DataSource):
            # `iri` refer to a DataSource
            if self.has(iri, hasDataValue):  # literal value
                return Value(
                    value=parse_literal(self.value(iri, hasDataValue)).to_python(),
                    unit=parse_literal(self.value(iri, hasUnit)).to_python()
                    if self.has(iri, hasUnit)
                    else None,
                    iri=self.value(iri, MAP.mapsTo),
                    cost=parse_literal(self.value(iri, hasCost)).to_python()
                    if self.has(iri, hasCost)
                    else 0.0,
                ).get_value(unit=unit, magnitude=magnitude, quantity=quantity)

            if self.has(iri, hasAccessFunction):  # callable
                func_iri = self.value(iri, hasAccessFunction)
                func = self.function_repo[func_iri]
                assert callable(func)  # nosec
                retval = func()
                if isinstance(retval, Value):
                    return retval.get_value(
                        unit=unit, magnitude=magnitude, quantity=quantity
                    )
                return retval

            raise TriplestoreError(
                f"data source {iri} has neither a 'hasDataValue' or a "
                f"'hasAccessFunction' property"
            )

        # `iri` correspond to an individual mapped to an ontological concept.
        # In this case we check if there exists a mapping route.
        routes = mapping_routes(
            target=iri,
            sources=list(self.subjects(RDF.type, DataSource)),
            triplestore=self,
            **kwargs,
        )
        if isinstance(routes, Value):
            return routes.get_value(unit=unit, magnitude=magnitude, quantity=quantity)
        return routes.eval(
            routeno=routeno,
            unit=unit,
            magnitude=magnitude,
            quantity=quantity,
        )
