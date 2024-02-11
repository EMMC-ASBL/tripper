"""A module that adds additional functionality to triplestore
"""

# pylint: disable=invalid-name,too-many-public-methods,too-many-lines
from __future__ import annotations  # Support Python 3.7 (PEP 585)

import uuid
from typing import TYPE_CHECKING

from tripper.errors import TriplestoreError
from tripper.literal import Literal
from tripper.namespace import MAP, RDF
from tripper.triplestore import (
    DataSource,
    Triplestore,
    hasAccessFunction,
    hasCost,
    hasDataValue,
    hasUnit,
)
from tripper.utils import parse_literal, random_string

if TYPE_CHECKING:  # pragma: no cover
    from typing import Any, Callable, Optional, Sequence, Union

    from tripper.mappings import Value


# Default packages in which to look for tripper backends
backend_packages = ["tripper.backends"]


class Tripper(Triplestore):
    """
    Class that provides additional
    methods for handling data in the triplestore,
    such as get_value, add_data and add_interpolation_source.
    """

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
            fn.__doc__ = (
                f"Function for data source: {data_source}.\n\n{func.__doc__}"
            )
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
            raise TypeError(
                f"`func` must be a callable or literal, got {type(func)}"
            )

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
                    value=parse_literal(
                        self.value(iri, hasDataValue)
                    ).to_python(),
                    unit=(
                        parse_literal(self.value(iri, hasUnit)).to_python()
                        if self.has(iri, hasUnit)
                        else None
                    ),
                    iri=self.value(iri, MAP.mapsTo),
                    cost=(
                        parse_literal(self.value(iri, hasCost)).to_python()
                        if self.has(iri, hasCost)
                        else 0.0
                    ),
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
            return routes.get_value(
                unit=unit, magnitude=magnitude, quantity=quantity
            )
        return routes.eval(
            routeno=routeno,
            unit=unit,
            magnitude=magnitude,
            quantity=quantity,
        )

    def add_interpolation_source(  # pylint: disable=too-many-arguments
        self,
        xcoord: str,
        ycoord: str,
        input_iri: str,
        output_iri: str,
        base_iri: "Optional[str]" = None,
        standard: str = "emmo",
        cost: "Optional[Union[float, Callable]]" = None,
        left: "Optional[float]" = None,
        right: "Optional[float]" = None,
        period: "Optional[float]" = None,
    ) -> str:
        """Add data source to triplestore, such that it can be used to
        transparently transform other data.

        No data will be fetch before it is actually needed.

        Parameters:
            xcoord: IRI of data source with x-coordinates `xp`.  Must be
                increasing if argument `period` is not specified. Otherwise,
                `xp` is internally sorted after normalising the periodic
                boundaries with ``xp = xp % period``.
            ycoord: IRI of data source with y-coordinates `yp`.  Must have
                the same length as `xp`.
            input_iri: IRI of ontological concept that interpolation input-
                data should be mapped to.
            output_iri: IRI of ontological concept that interpolation output-
                data should be mapped to.
            base_iri: Base of the IRI representing the transformation in the
                knowledge base.  Defaults to the base IRI of the triplestore.
            standard: Name of ontology to use when describing the
                transformation.  Valid values are:
                - "emmo": Elementary Multiperspective Material Ontology (EMMO)
                - "fno": Function Ontology (FnO)
            cost: User-defined cost of following this mapping relation
                represented as a float.  It may be given either as a
                float or as a callable taking the same arguments as `func`
                returning the cost as a float.
            left: Value to return for `x < xp[0]`, default is `fp[0]`.
            right: Value to return for `x > xp[-1]`, default is `fp[-1]`.
            period: A period for the x-coordinates. This parameter allows the
                proper interpolation of angular x-coordinates. Parameters
                `left` and `right` are ignored if `period` is specified.

        Returns:
            transformation_iri: IRI of the added transformation.

        """
        try:
            import numpy as np  # pylint: disable=import-outside-toplevel
        except ImportError as exc:
            raise RuntimeError(
                "Triplestore.add_interpolation_source() requires numpy.\n"
                "Install it with\n\n"
                "    pip install numpy"
            ) from exc

        def func(x):
            xp = self.get_value(xcoord)
            fp = self.get_value(ycoord)
            return np.interp(
                x,
                xp=xp,
                fp=fp,
                left=left,
                right=right,
                period=period,
            )

        return self.add_function(
            func,
            expects=input_iri,
            returns=output_iri,
            base_iri=base_iri,
            standard=standard,
            cost=cost,
        )
