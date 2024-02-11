"""Implements mappings between entities.

Units are currently handled with pint.Quantity.  The benefit of this
compared to explicit unit conversions, is that units will be handled
transparently by mapping functions, without any need to specify units
of input and output parameters.

Shapes are automatically handled by expressing non-scalar quantities
with numpy.

"""

# pylint: disable=invalid-name,redefined-builtin,too-many-lines
from __future__ import annotations  # Support Python 3.7 (PEP 585)

import subprocess  # nosec: B404
from collections import defaultdict
from enum import Enum
from typing import TYPE_CHECKING, Mapping, Sequence

from pint import Quantity  # remove

from tripper import DM, EMMO, FNO, MAP, RDF, RDFS
from tripper.errors import CannotGetFunctionError
from tripper.triplestore import hasAccessFunction, hasDataValue
from tripper.utils import parse_literal

if TYPE_CHECKING:  # pragma: no cover
    from typing import Any, Callable, Dict, List, Optional, Tuple, Type, Union

    from tripper import Triplestore

    # Add some specialised types for convinience
    Input = Union["MappingStep", "Value"]
    Inputs = Dict[str, Input]


class MappingError(Exception):
    """Base class for mapping errors."""


class InsufficientMappingError(MappingError):
    """There are properties or dimensions that are not mapped."""


class AmbiguousMappingError(MappingError):
    """A property maps to more than one value."""


class InconsistentDimensionError(MappingError):
    """The size of a dimension is assigned to more than one value."""


class InconsistentTriplesError(MappingError):
    """Inconsistcy in RDF triples."""


class MissingRelationError(MappingError):
    """There are missing relations in RDF triples."""


class UnknownUnitError(MappingError):
    """A unit does not exists in the pint unit registry."""


class StepType(Enum):
    """Type of mapping step when going from the output to the inputs."""

    UNSPECIFIED = 0
    MAPSTO = 1
    INV_MAPSTO = -1
    INSTANCEOF = 2
    INV_INSTANCEOF = -2
    SUBCLASSOF = 3
    INV_SUBCLASSOF = -3
    FUNCTION = 4


class Value:
    """Represents the value of an instance property.

    Arguments:
        value: Property value.
        unit: Property unit.
        iri: IRI of ontological concept that this value is an instance of.
        property_iri: IRI of datamodel property that this value is an
            instance of.
        cost: Cost of accessing this value.
    """

    # pylint: disable=too-few-public-methods

    def __init__(
        self,
        value: "Any" = None,
        unit: "Optional[str]" = None,
        iri: "Optional[str]" = None,
        property_iri: "Optional[str]" = None,
        cost: "Union[float, Callable]" = 0.0,
    ):
        self._value = value
        self.unit = unit
        if iri:
            self.output_iri = iri
        elif hasattr(value, __name__):
            self.output_iri = value.__name__
        else:
            self.output_iri = f"_:value_{id(value)}"
        self.property_iri = property_iri
        self.cost = cost

    value = property(
        lambda self: self._value() if callable(self._value) else self._value,
        doc="Value of property.",
    )

    def __repr__(self):
        args = []
        if self.unit:
            args.append(f", unit={self.unit}")
        if self.output_iri:
            args.append(f", iri={self.output_iri}")
        if self.property_iri:
            args.append(f", property_iri={self.property_iri}")
        if self.cost:
            args.append(f", cost={self.cost}")
        return f"Value({self._value!r}{''.join(args)})"

    def get_value(self, unit=None, magnitude=False, quantity=None) -> "Any":
        """Returns the evaluated value of given input route number.

        Arguments:
            unit: return the result in the given unit.
                Implies `magnitude=True`.
            magnitude: Whether to only return the magnitude of the evaluated
                value (with no unit).
            quantity: Quantity class to use for evaluation.  Defaults to pint.

        Returns:
            Value.
        """
        if quantity is None:
            quantity = Quantity
        value = self._value() if callable(self._value) else self._value
        if not isinstance(value, Quantity) and not self.unit:
            return value
        q = quantity(value, self.unit)
        if unit:
            return q.m_as(unit)
        if magnitude:
            return q.m
        return q

    def show(
        self,
        routeno: "Optional[int]" = None,
        name: "Optional[str]" = None,
        indent: int = 0,
    ) -> str:
        # pylint: disable=unused-argument
        """Returns a string representation of the Value.

        Arguments:
            routeno: Unused.  The argument exists for consistency with
                the corresponding method in Step.
            name: Name of value.
            indent: Indentation level.

        Returns:
            String representation of the value.
        """
        strings = []
        ind = " " * indent
        strings.append(ind + f'{name if name else "Value"}:')
        strings.append(ind + f"  iri: {self.output_iri}")
        strings.append(ind + f"  property_iri: {self.property_iri}")
        strings.append(ind + f"  unit: {self.unit}")
        strings.append(ind + f"  cost: {self.cost}")
        strings.append(ind + f"  value: {self.value}")
        return "\n".join(strings)


class MappingStep:
    """A step in a mapping route from a target to one or more sources.

    A mapping step corresponds to one or more RDF triples.  In the
    simple case of a `mo:mapsTo` or `rdfs:isSubclassOf` relation, it is
    only one triple.  For transformations that has several input and
    output, a set of triples are expected.

    Arguments:
        output_iri: IRI of the output concept.
        steptype: One of the step types from the StepType enum.
        function: Callable that evaluates the output from the input.
        cost: The cost related to this mapping step.  Should be either a
            float or a callable taking three arguments (`triplestore`,
            `input_iris` and `output_iri`) and return the cost as a float.
        output_unit: Output unit.
        triplestore: Triplestore instance containing the knowledge base
            that this mapping step was created from.

    The arguments can also be assigned as attributes.
    """

    # pylint: disable=too-many-instance-attributes

    def __init__(
        self,
        output_iri: str,
        steptype: "StepType" = StepType.UNSPECIFIED,
        function: "Optional[Callable]" = None,
        cost: "Union[float, Callable]" = 1.0,
        output_unit: "Optional[str]" = None,
        triplestore: "Optional[Triplestore]" = None,
    ) -> None:
        self.output_iri = output_iri
        self.steptype = steptype
        self.function = function
        self.cost = cost
        self.triplestore = triplestore
        self.output_unit = output_unit
        self.input_routes: "List[dict]" = []  # list of inputs dicts
        self.join_mode = False  # whether to join upcoming input
        self.joined_input: "Inputs" = {}

    def add_inputs(self, inputs: "Inputs") -> None:
        """Add input Mapping (e.g., dict) for an input route."""
        assert isinstance(inputs, Mapping)  # nosec B101
        self.input_routes.append(inputs)

    def add_input(self, input: "Input", name: "Optional[str]" = None) -> None:
        """Add an input (MappingStep or Value), where `name` is the name
        assigned to the argument.

        If the `join_mode` attribute is false, a new route is created with
        only one input.

        If the `join_mode` attribute is true, the input is remembered, but
        first added when `join_input()` is called.

        Arguments:
            input: A mapping step or a value.
            name: Name assigned to the argument.
        """
        assert isinstance(input, (MappingStep, Value))  # nosec B101
        argname = name if name else f"arg{len(self.joined_input)+1}"
        if self.join_mode:
            self.joined_input[argname] = input
        else:
            self.add_inputs({argname: input})

    def join_input(self) -> None:
        """Join all input added with add_input() since `join_mode` was set
        true.  Resets `join_mode` to false."""
        if not self.join_mode:
            raise MappingError("Calling join_input() when join_mode is false.")
        self.join_mode = False
        self.add_inputs(self.joined_input)
        self.joined_input = {}

    def eval(
        self,
        routeno: "Optional[int]" = None,
        unit: "Optional[str]" = None,
        magnitude: bool = False,
        quantity: "Optional[Type[Quantity]]" = None,
    ) -> "Any":
        """Returns the evaluated value of given input route number.

        Arguments:
            routeno: The route number to evaluate.  If None (default)
                the route with the lowest cost is evalueated.
            unit: return the result in the given unit.
                Implies `magnitude=True`.
            magnitude: Whether to only return the magnitude of the evaluated
                value (with no unit).
            quantity: Quantity class to use for evaluation.  Defaults to pint.

        Returns:
            Evaluation result.
        """
        if not self.number_of_routes():
            raise MissingRelationError(
                f"no route to evaluate '{self.output_iri}'"
            )
        if quantity is None:
            quantity = Quantity
        if routeno is None:
            ((_, routeno),) = self.lowest_costs(nresults=1)
        inputs, idx = self.get_inputs(routeno)
        values = get_values(inputs, idx, quantity=quantity)

        # if len(inputs) == 1 and all(
        #    isinstance(v, Value) for v in inputs.values()
        # ):
        #    (value,) = tuple(inputs.values())
        # elif self.function:
        if self.function:
            value = self.function(**values)
        elif len(values) == 1:
            (value,) = values.values()
        else:
            raise TypeError(
                f"Expected inputs to be a single argument: {values}"
            )

        if isinstance(value, Quantity) and unit:
            return value.m_as(unit)
        if isinstance(value, Quantity) and magnitude:
            return value.m
        if isinstance(value, Value):
            return value.get_value(
                unit=unit, magnitude=magnitude, quantity=quantity
            )
        return value

    def get_inputs(self, routeno: int) -> "Tuple[Inputs, int]":
        """Returns input and input index `(inputs, idx)` for route number
        `routeno`.

        Arguments:
            routeno: The route number to return inputs for.

        Returns:
            Inputs and difference between route number and number of routes for
            an input dictioary.
        """
        n = 0
        for inputs in self.input_routes:
            n0 = n
            n += get_nroutes(inputs)
            if n > routeno:
                return inputs, routeno - n0
        raise ValueError(f"routeno={routeno} exceeds number of routes")

    def get_input_iris(self, routeno: int) -> "Dict[str, Optional[str]]":
        """Returns a dict mapping input names to iris for the given route
        number.

        Arguments:
            routeno: The route number to return a mapping for.

        Returns:
            Mapping of input names to IRIs.

        """
        inputs, _ = self.get_inputs(routeno)
        return {
            k: v.output_iri if isinstance(v, MappingStep) else v.output_iri
            for k, v in inputs.items()
        }

    def number_of_routes(self) -> int:
        """Total number of routes to this mapping step.

        Returns:
            Total number of routes to this mapping step.
        """
        n = 0
        for inputs in self.input_routes:
            n += get_nroutes(inputs)
        return n

    def lowest_costs(self, nresults: int = 5) -> "List[Tuple[float, int]]":
        """Returns a list of `(cost, routeno)` tuples with up to the `nresult`
        lowest costs and their corresponding route numbers.

        Arguments:
            nresults: Number of results to return.

        Returns:
            A list of `(cost, routeno)` tuples.
        """
        try:
            import numpy as np  # pylint: disable=import-outside-toplevel
        except ImportError as exc:
            raise RuntimeError(
                "Mappings.lowest_costs() requires numpy.\n"
                "Install it with\n\n"
                "    pip install numpy"
            ) from exc

        result = []
        n = 0  # total number of routes

        # Loop over all toplevel routes leading into this mapping step
        for inputs in self.input_routes:
            # For each route, loop over all input arguments of this step
            # The number of permutations we must consider is the product
            # of the total number of routes to each input argument.
            #
            # We (potentially drastic) limit the possibilities by only
            # considering the `nresults` routes with lowest costs into
            # each argument.  This gives at maximum
            #
            #     nresults * number_of_input_arguments
            #
            # possibilities. We calculate the costs for all of them and
            # store them in an array with two columns: `cost` and `routeno`.
            # The `results` list is extended with the cost array
            # for each toplevel route leading into this step.
            base = np.rec.fromrecords(
                [(0.0, 0)], names="cost,routeno", formats="f8,i8"
            )
            m = 1
            for input in inputs.values():
                if isinstance(input, MappingStep):
                    nroutes = input.number_of_routes()
                    res = np.rec.fromrecords(
                        sorted(
                            input.lowest_costs(nresults=nresults),
                            key=lambda x: x[1],
                        ),
                        # [
                        #     row
                        #     for row in sorted(
                        #         input.lowest_costs(nresults=nresults),
                        #         key=lambda x: x[1],
                        #     )
                        # ],
                        dtype=base.dtype,
                    )
                    res1 = res.repeat(len(base))
                    base = np.tile(base, len(res))
                    base.cost += res1.cost
                    base.routeno += res1.routeno * m
                    m *= nroutes
                else:
                    base.cost += input.cost

            # Reduce the length of base (makes probably only sense in
            # the case self.cost is a callable, but it doesn't hurt...)
            base.sort()
            base = base[:nresults]
            base.routeno += n
            n += m

            # Add the cost for this step to `res`.  If `self.cost` is
            # a callable, we call it with the input for each routeno
            # as arguments.  Otherwise `self.cost` is the cost of this
            # mapping step.
            if callable(self.cost):
                for i, rno in enumerate(base.routeno):
                    inputs, _ = self.get_inputs(rno)
                    input_iris = [
                        input.output_iri for input in inputs.values()
                    ]
                    owncost = self.cost(
                        self.triplestore, input_iris, self.output_iri
                    )
                    base.cost[i] += owncost
            else:
                owncost = self.cost
                base.cost += owncost

            result.extend(base.tolist())

        # Finally sort the results according to cost and return the
        # `nresults` rows with lowest cost.
        return sorted(result)[:nresults]

    def show(
        self,
        routeno: "Optional[int]" = None,
        name: "Optional[str]" = None,
        indent: int = 0,
    ) -> str:
        """Returns a string representation of the mapping routes to this step.

        Arguments:
            routeno: show given route.  The default is to show all routes.
            name: Name of the last mapping step (mainly for internal use).
            indent: How of blanks to prepend each line with (mainly for
                internal use).

        Returns:
            String representation of the mapping routes.
        """
        strings = []
        ind = " " * indent
        strings.append(ind + f'{name if name else "Step"}:')
        strings.append(
            ind + f"  steptype: "
            f"{self.steptype.name if self.steptype else None}"
        )
        strings.append(ind + f"  output_iri: {self.output_iri}")
        strings.append(ind + f"  output_unit: {self.output_unit}")
        strings.append(ind + f"  cost: {self.cost}")
        if routeno is None:
            strings.append(ind + "  routes:")
            for inputs in self.input_routes:
                t = "\n".join(
                    [
                        input_.show(name=name_, indent=indent + 6)
                        for name_, input_ in inputs.items()
                    ]
                )
                strings.append(ind + "    - " + t[indent + 6 :])
        else:
            strings.append(ind + "  inputs:")
            inputs, idx = self.get_inputs(routeno)
            t = "\n".join(
                [
                    input_.show(routeno=idx, name=name_, indent=indent + 6)
                    for name_, input_ in inputs.items()
                ]
            )
            strings.append(ind + "    - " + t[indent + 6 :])
        return "\n".join(strings)

    def _iri(self, iri: str) -> str:
        """Help method that returns prefixed iri if possible, otherwise
        `iri`."""
        return self.triplestore.prefix_iri(iri) if self.triplestore else iri

    def _visualise(
        self, routeno: int, next_iri: str, next_steptype: StepType
    ) -> str:
        """Help function for visualise().

        Arguments:
            routeno: Route number to visualise.
            next_iri: IRI of the next mapping step (i.e. the previous mapping
                when starting from the target).
            next_steptype: Step type from this to next iri.

        Returns:
            Mapping route in dot (graphviz) notation.
        """
        hasOutput = EMMO.EMMO_c4bace1d_4db0_4cd3_87e9_18122bae2840

        # Edge labels. We invert the steptypes, since we want to visualise
        # the workflow in forward direction, while the steptypes refer to
        # backward direction
        labeldict = {
            StepType.UNSPECIFIED: "",
            StepType.MAPSTO: "inverse(mapsTo)",
            StepType.INV_MAPSTO: "mapsTo",
            StepType.INSTANCEOF: "instanceOf",
            StepType.INV_INSTANCEOF: "inverse(instanceOf)",
            StepType.SUBCLASSOF: "subClassOf",
            StepType.INV_SUBCLASSOF: "inverse(subClassOf)",
            StepType.FUNCTION: "function",
        }
        inputs, idx = self.get_inputs(routeno)
        strings = []
        for _, input in inputs.items():
            if isinstance(input, Value):
                strings.append(
                    f'  "{self._iri(input.output_iri)}" -> '
                    f'"{self._iri(self.output_iri)}" '
                    f'[label="{labeldict[self.steptype]}"];'
                )
            elif isinstance(input, MappingStep):
                strings.append(
                    input._visualise(  # pylint: disable=protected-access
                        routeno=idx,
                        next_iri=self.output_iri,
                        next_steptype=self.steptype,
                    )
                )
            else:
                raise TypeError("input should be Value or MappingStep")
        if next_iri:
            label = labeldict[next_steptype]
            if next_steptype == StepType.FUNCTION and self.triplestore:
                model_iri = self.triplestore.value(
                    predicate=hasOutput,  # Assuming EMMO
                    object=next_iri,
                    default="function",
                    any=True,
                )
                if model_iri:
                    label = self.triplestore.value(
                        subject=model_iri,
                        predicate=RDFS.label,
                        default=self._iri(model_iri),
                        any=True,
                    )
            else:
                label = labeldict[next_steptype]
            strings.append(
                f'  "{self._iri(self.output_iri)}" -> '
                f'"{self._iri(next_iri)}" [label="{label}"];'
            )
        return "\n".join(strings)

    def visualise(
        self,
        routeno: int,
        output: "Optional[str]" = None,
        format: "Optional[str]" = "png",
        dot: str = "dot",
    ) -> str:
        """Greate a Graphviz visualisation of a given mapping route.

        Arguments:
            routeno: Number of mapping route to visualise.
            output: If given, write the graph to this file.
            format: File format to use with `output`.
            dot: Path to Graphviz dot executable.

        Returns:
            String representation of the graph in dot format.
        """
        strings = []
        strings.append("digraph G {")
        strings.append(self._visualise(routeno, "", StepType.UNSPECIFIED))
        strings.append("}")
        graph = "\n".join(strings) + "\n"
        if output:
            subprocess.run(
                args=[dot, f"-T{format}", "-o", output],
                shell=False,  # nosec: B603
                check=True,
                input=graph.encode(),
            )
        return graph


def get_nroutes(inputs: "Inputs") -> int:
    """Help function returning the number of routes for an input dict.

    Arguments:
        inputs: Input dictionary.

    Returns:
        Number of routes in the `inputs` input dictionary.
    """
    nroutes = 1
    for input in inputs.values():
        if isinstance(input, MappingStep):
            nroutes *= input.number_of_routes()
    return nroutes


def get_values(
    inputs: "dict[str, Any]",
    routeno: int,
    quantity: "Type[Quantity]" = Quantity,
    magnitudes: bool = False,
) -> "dict[str, Any]":
    """Help function returning a dict mapping the input names to actual value
    of expected input unit.

    There exists `get_nroutes(inputs)` routes to populate `inputs`.
    `routeno` is the index of the specific route we will use to obtain the
    values.

    Arguments:
        inputs: Input dictionary.
        routeno: Route number index.
        quantity: A unit quantity class.
        magnitudes: Whether to only return the magnitude of the evaluated
            value (with no unit).

    Returns:
        A mapping between input names and values of expected input unit.
    """
    values = {}
    for k, v in inputs.items():
        if isinstance(v, MappingStep):
            value = v.eval(routeno=routeno, quantity=quantity)
            values[k] = (
                value.to(v.output_unit)
                if v.output_unit and isinstance(v, quantity)
                else value
            )
        elif isinstance(v, Value):
            values[k] = v.value if not v.unit else quantity(v.value, v.unit)
        else:
            raise TypeError(
                "Expected values in inputs to be either `MappingStep` or "
                "`Value` objects."
            )

        if magnitudes:
            values = {
                k: v.m if isinstance(v, quantity) else v
                for k, v in values.items()
            }

    return values


def emmo_mapper(triplestore: "Triplestore") -> "Dict[str, list]":
    """Finds all function definitions in `triplestore` based on EMMO.

    Return a dict mapping output IRIs to a list of

        (function_iri, [input_iris, ...])

    tuples.
    """
    Task = EMMO.EMMO_4299e344_a321_4ef2_a744_bacfcce80afc
    hasInput = EMMO.EMMO_36e69413_8c59_4799_946c_10b05d266e22
    hasOutput = EMMO.EMMO_c4bace1d_4db0_4cd3_87e9_18122bae2840

    d = defaultdict(list)
    for task in triplestore.subjects(RDF.type, Task):
        inputs = list(triplestore.objects(task, hasInput))
        for output in triplestore.objects(task, hasOutput):
            d[output].append((task, inputs))

    return d


def fno_mapper(triplestore: "Triplestore") -> "Dict[str, list]":
    """Finds all function definitions in `triplestore` based on the function
    ontololy (FNO).

    Arguments:
        triplestore: The triplestore to investigate.

    Returns:
        A mapping of output IRIs to a list of

            (function_iri, [input_iris, ...])

        tuples.
    """
    # pylint: disable=too-many-branches

    # Temporary dicts for fast lookup
    Dfirst = dict(triplestore.subject_objects(RDF.first))
    Drest = dict(triplestore.subject_objects(RDF.rest))
    Dexpects = defaultdict(list)
    Dreturns = defaultdict(list)
    for s, o in triplestore.subject_objects(FNO.expects):
        Dexpects[s].append(o)
    for s, o in triplestore.subject_objects(FNO.returns):
        Dreturns[s].append(o)

    d = defaultdict(list)
    for func, lst in Dreturns.items():
        input_iris = []
        for exp in Dexpects.get(func, ()):
            if exp in Dfirst:
                while exp in Dfirst:
                    input_iris.append(Dfirst[exp])
                    if exp not in Drest:
                        break
                    exp = Drest[exp]
            else:
                # Support also misuse of FNO, where fno:expects refers
                # directly to input individuals
                input_iris.append(exp)

        for ret in lst:
            if ret in Dfirst:
                while ret in Dfirst:
                    d[Dfirst[ret]].append((func, input_iris))
                    if ret not in Drest:
                        break
                    ret = Drest[ret]
            else:
                # Support also misuse of FNO, where fno:returns refers
                # directly to the returned individual
                d[ret].append((func, input_iris))

    return d


def mapping_routes(
    target: str,
    sources: "Union[Dict[str, Union[Value, None]], Sequence[str]]",
    triplestore: "Triplestore",
    function_repo: "Optional[dict]" = None,
    function_mappers: "Union[str, Sequence[Callable]]" = (
        emmo_mapper,
        fno_mapper,
    ),
    default_costs: "Tuple" = (
        ("function", 10.0),
        ("mapsTo", 2.0),
        ("instanceOf", 1.0),
        ("subClassOf", 1.0),
        ("value", 0.0),
    ),
    value_class: "Optional[Type[Value]]" = None,
    mappingstep_class: "Optional[Type[MappingStep]]" = None,
    mapsTo: str = MAP.mapsTo,
    instanceOf: str = DM.instanceOf,
    subClassOf: str = RDFS.subClassOf,
    # description: str = DCTERMS.description,
    label: str = RDFS.label,
    hasUnit: str = DM.hasUnit,
    hasCost: str = DM.hasCost,  # TODO - add hasCost to the DM ontology
    hasAccessFunction: str = hasAccessFunction,  # pylint: disable=redefined-outer-name
    hasDataValue: str = hasDataValue,  # pylint: disable=redefined-outer-name
) -> Input:
    """Find routes of mappings from any source in `sources` to `target`.

    This implementation supports functions (using FnO) and subclass
    relations.  It also correctly handles transitivity of `mapsTo` and
    `subClassOf` relations.

    Arguments:
        target: IRI of the target in `triplestore`.
        sources: Dict mapping source IRIs to source values or a sequence
            of source IRIs (with no explicit values).
        triplestore: Triplestore instance for the knowledge graph to traverse.

    Additional arguments for fine-grained tuning:
        function_repo: Dict mapping function IRIs to corresponding Python
            function.  Default is to use `triplestore.function_repo`.
        function_mappers: Name of mapping standard: "emmo" or "fno".
            Alternatively, a sequence of mapping functions that takes
            `triplestore` as argument and return a dict mapping output IRIs
            to a list of `(function_iri, [input_iris, ...])` tuples.
        default_costs: A dict providing default costs of different types
            of mapping steps ("function", "mapsTo", "instanceOf",
            "subclassOf", and "value").  These costs can be overridden with
            'hasCost' relations in the ontology.
        value_class: Optional `Value` subclass to use instead of `Value` when
            creating the returned mapping route.
        mappingstep_class: Optional `MappingStep` subclass to use instead of
            `MappingStep` when creating the returned mapping route.
        mapsTo: IRI of 'mapsTo' in `triplestore`.
        instanceOf: IRI of 'instanceOf' in `triplestore`.
        subClassOf: IRI of 'subClassOf' in `triples`.  Set it to None if
            subclasses should not be considered.
        label: IRI of 'label' in `triplestore`.  Used for naming function
            input parameters.  The default is to use rdfs:label.
        hasUnit: IRI of 'hasUnit' in `triplestore`.  Can be used to explicit
            specify the unit of a quantity.
        hasCost: IRI of 'hasCost' in `triplestore`.  Used for associating a
            user-defined cost or cost function with instantiation of a
            property.
        hasAccessFunction: IRI of 'hasAccessFunction'.  Used to associate a
            data source to a function that retrieves the data.
        hasDataValue: IRI of 'hasDataValue'.  Used to associate a data source
            with its literal value.

    Returns:
        A MappingStep instance.  This is a root of a nested tree of
        MappingStep instances providing an (efficient) internal description
        of all possible mapping routes from `sources` to `target`.
    """
    # pylint: disable=too-many-arguments,too-many-locals,too-many-statements

    if target in sources:
        return Value(iri=target)

    if isinstance(sources, Sequence):
        sources = {iri: None for iri in sources}

    if function_repo is None:
        function_repo = triplestore.function_repo

    if isinstance(function_mappers, str):
        fmd = {"emmo": emmo_mapper, "fno": fno_mapper}
        function_mappers = [fmd[name] for name in function_mappers.split(",")]

    default_costs = dict(default_costs)

    if value_class is None:
        value_class = Value

    if mappingstep_class is None:
        mappingstep_class = MappingStep

    # Create lookup tables for fast access to triplestore content
    soMaps = defaultdict(list)  # (s, mapsTo, o)     ==> soMaps[s]  -> [o, ..]
    osMaps = defaultdict(
        list
    )  # (o, inv(mapsTo), s)     ==> osMaps[o]  -> [s, ..]
    osSubcl = defaultdict(
        list
    )  # (o, inv(subClassOf), s) ==> osSubcl[o] -> [s, ..]
    soInst = {}  # (s, instanceOf, o) ==> soInst[s]  -> o
    osInst = defaultdict(
        list
    )  # (o, inv(instanceOf), s) ==> osInst[o]  -> [s, ..]
    for s, o in triplestore.subject_objects(mapsTo):
        soMaps[s].append(o)
        osMaps[o].append(s)
    for s, o in triplestore.subject_objects(subClassOf):
        osSubcl[o].append(s)
    for s, o in triplestore.subject_objects(instanceOf):
        if s in soInst:
            raise InconsistentTriplesError(
                f"The same individual can only relate to one datamodel "
                f"property via {instanceOf} relations."
            )
        soInst[s] = o
        osInst[o].append(s)
    soName = dict(triplestore.subject_objects(label))
    soUnit = dict(triplestore.subject_objects(hasUnit))
    soCost = dict(triplestore.subject_objects(hasCost))
    soAFun = dict(triplestore.subject_objects(hasAccessFunction))
    soDVal = dict(triplestore.subject_objects(hasDataValue))

    def getfunc(func_iri, default=None):
        """Returns callable function corresponding to `func_iri`.
        Raises CannotGetFunctionError if func_iri cannot be found."""
        if func_iri is None:
            return None
        if func_iri in function_repo and function_repo[func_iri]:
            return function_repo[func_iri]
        try:
            return (
                triplestore._get_function(  # pylint: disable=protected-access
                    func_iri
                )
            )
        except CannotGetFunctionError:
            return default

    def getcost(target, stepname):
        """Returns the cost assigned to IRI `target` for a mapping step
        of type `stepname`."""
        cost = soCost.get(target, default_costs[stepname])
        if cost is None or callable(cost) or isinstance(cost, float):
            return cost
        return getfunc(cost, float(parse_literal(cost)))

    def walk(target, visited, step):
        """Walk backward in rdf graph from `node` to sources."""
        if target in visited:
            return
        visited.add(target)

        def addnode(node, steptype, stepname):
            if node in visited:
                return
            step.steptype = steptype
            step.cost = getcost(target, stepname)
            if node in soAFun:
                value = value_class(
                    value=getfunc(soAFun[node]),
                    unit=soUnit.get(node),
                    iri=node,
                    property_iri=soInst.get(node),
                    cost=getcost(node, "value"),
                )
                step.add_input(value, name=soName.get(node))
            elif node in soDVal:
                literal = parse_literal(soDVal[node])
                value = value_class(
                    value=literal.to_python(),
                    unit=soUnit.get(node),
                    iri=node,
                    property_iri=soInst.get(node),
                    cost=getcost(node, "value"),
                )
                step.add_input(value, name=soName.get(node))
            elif node in sources:
                value = value_class(
                    value=sources[node],
                    unit=soUnit.get(node),
                    iri=node,
                    property_iri=soInst.get(node),
                    cost=getcost(node, "value"),
                )
                step.add_input(value, name=soName.get(node))
            else:
                prevstep = mappingstep_class(
                    output_iri=node,
                    output_unit=soUnit.get(node),
                    triplestore=triplestore,
                )
                step.add_input(prevstep, name=soName.get(node))
                walk(node, visited, prevstep)

        for node in osInst[target]:
            addnode(node, StepType.INV_INSTANCEOF, "instanceOf")

        for node in soMaps[target]:
            addnode(node, StepType.MAPSTO, "mapsTo")

        for node in osMaps[target]:
            addnode(node, StepType.INV_MAPSTO, "mapsTo")

        for node in osSubcl[target]:
            addnode(node, StepType.INV_SUBCLASSOF, "subClassOf")

        for fmap in function_mappers:
            for func_iri, input_iris in fmap(triplestore)[target]:
                step.steptype = StepType.FUNCTION
                step.cost = getcost(func_iri, "function")
                step.function = getfunc(func_iri)
                step.join_mode = True
                for input_iri in input_iris:
                    step0 = mappingstep_class(
                        output_iri=input_iri,
                        output_unit=soUnit.get(input_iri),
                        triplestore=triplestore,
                    )
                    step.add_input(step0, name=soName.get(input_iri))
                    walk(input_iri, visited, step0)
                step.join_input()

    visited = set()
    step = mappingstep_class(
        output_iri=target,
        output_unit=soUnit.get(target),
        triplestore=triplestore,
    )
    if target in soInst:
        # It is only initially we want to follow instanceOf in forward
        # direction.  Later on we will only follow mapsTo and instanceOf in
        # backward direction.
        visited.add(target)  # do we really wan't this?  Yes, I think so...
        source = soInst[target]
        step.steptype = StepType.INSTANCEOF
        step.cost = getcost(source, "instanceOf")
        step0 = mappingstep_class(
            output_iri=source,
            output_unit=soUnit.get(source),
            triplestore=triplestore,
        )
        step.add_input(step0, name=soName.get(target))
        step = step0
        target = source

    if target not in soMaps:
        raise MissingRelationError(f'Missing "mapsTo" relation on: {target}')
    walk(target, visited, step)

    return step
