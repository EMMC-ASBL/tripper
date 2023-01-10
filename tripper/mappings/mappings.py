"""Implements mappings between entities.

Units are currently handled with pint.Quantity.  The benefit of this
compared to explicit unit conversions, is that units will be handled
transparently by mapping functions, without any need to specify units
of input and output parameters.

Shapes are automatically handled by expressing non-scalar quantities
with numpy.

"""
# pylint: disable=invalid-name,redefined-builtin
from __future__ import annotations  # Support Python 3.7 (PEP 585)

from collections import defaultdict
from enum import Enum
from typing import TYPE_CHECKING

import numpy as np
from pint import Quantity  # remove

from tripper import DM, FNO, MAP, RDF, RDFS

if TYPE_CHECKING:  # pragma: no cover
    from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple, Union

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


class StepType(Enum):
    """Type of mapping step when going from the output to the inputs."""

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
        value: "Any",
        unit: "Optional[str]" = None,
        iri: "Optional[str]" = None,
        property_iri: "Optional[str]" = None,
        cost: float = 0.0,
    ):
        self.value = value
        self.unit = unit
        self.iri = iri
        self.property_iri = property_iri
        self.cost = cost

    def show(
        self,
        routeno: "Optional[int]" = None,
        name: "Optional[str]" = None,
        indent: int = 0,
    ):  # pylint: disable=unused-argument
        """Returns a string representation of the Value.

        Arguments:
            routeno: Unused.  The argument exists for consistency with
                the corresponding method in Step.
            name: Name of value.
            indent: Indentation level.
        """
        strings = []
        ind = " " * indent
        strings.append(ind + f'{name if name else "Value"}:')
        strings.append(ind + f"  iri: {self.iri}")
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
            float or a callable taking the same arguments as `function` as
            input returning the cost as a float.
        output_unit: Output unit.

    The arguments can also be assigned as attributes.
    """

    # pylint: disable=too-many-instance-attributes

    def __init__(
        self,
        output_iri: "Optional[str]" = None,
        steptype: "Optional[StepType]" = None,
        function: "Optional[Callable]" = None,
        cost: "Union[float, Callable]" = 1.0,
        output_unit: "Optional[str]" = None,
    ):
        self.output_iri = output_iri
        self.steptype = steptype
        self.function = function
        self.cost = cost
        self.output_unit = output_unit
        self.input_routes: "List[dict]" = []  # list of inputs dicts
        self.join_mode = False  # whether to join upcoming input
        self.joined_input: "Inputs" = {}

    def add_inputs(self, inputs: "Inputs"):
        """Add input dict for an input route."""
        assert isinstance(inputs, dict)  # nosec
        self.input_routes.append(inputs)

    def add_input(self, input: "Input", name: "Optional[str]" = None):
        """Add an input (MappingStep or Value), where `name` is the name
        assigned to the argument.

        If the `join_mode` attribute is false, a new route is created with
        only one input.

        If the `join_mode` attribute is true, the input is remembered, but
        first added when join_input() is called.
        """
        assert isinstance(input, (MappingStep, Value))  # nosec
        argname = name if name else f"arg{len(self.joined_input)+1}"
        if self.join_mode:
            self.joined_input[argname] = input
        else:
            self.add_inputs({argname: input})

    def join_input(self):
        """Join all input added with add_input() since `join_mode` was set true.
        Resets `join_mode` to false."""
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
        quantity: "Any" = Quantity,
    ) -> "Any":
        """Returns the evaluated value of given input route number.

        Args:
            routeno: The route number to evaluate.  If None (default)
                the route with the lowest cost is evalueated.
            unit: return the result in the given unit.
                Implies `magnitude=True`.
            magnitude: Whether to only return the magitude of the evaluated
                value (with no unit).
            quantity: Quantity class to use for evaluation.  Defaults to pint.

        Returns:
            Evaluation result.
        """
        if routeno is None:
            ((_, routeno),) = self.lowest_costs(nresults=1)
        inputs, idx = self.get_inputs(routeno)
        values = get_values(inputs, idx, quantity=quantity)
        if self.function:
            value = self.function(**values)
        elif len(values) == 1:
            (value,) = values.values()
        else:
            raise TypeError(f"Expected inputs to be a single argument: {values}")

        if isinstance(value, quantity) and unit:
            return value.m_as(unit)
        if isinstance(value, quantity) and magnitude:
            return value.m
        return value

    def get_inputs(self, routeno: int) -> "Tuple[Inputs, int]":
        """Returns input and input index `(inputs, idx)` for route number
        `routeno`."""
        n = 0
        for inputs in self.input_routes:
            n0 = n
            n += get_nroutes(inputs)
            if n > routeno:
                return inputs, routeno - n0
        raise ValueError(f"routeno={routeno} exceeds number of routes")

    def get_input_iris(self, routeno: int) -> "Dict[str, Optional[str]]":
        """Returns a dict mapping input names to iris for the given route
        number."""
        inputs, _ = self.get_inputs(routeno)
        return {
            k: v.output_iri if isinstance(v, MappingStep) else v.iri
            for k, v in inputs.items()
        }

    def number_of_routes(self) -> int:
        """Returns total number of routes to this mapping step."""
        n = 0
        for inputs in self.input_routes:
            n += get_nroutes(inputs)
        return n

    def lowest_costs(self, nresults: int = 5) -> "List[Tuple[float, int]]":
        """Returns a list of `(cost, routeno)` tuples with up to the `nresult`
        lowest costs and their corresponding route numbers."""
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
            base = np.rec.fromrecords([(0.0, 0)], names="cost,routeno", formats="f8,i8")
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
                    values = get_values(inputs, rno, magnitudes=True)
                    owncost = self.cost(**values)
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
    ):
        """Returns a string representation of the mapping routes to this step.

        Arguments:
            routeno: show given route.  The default is to show all routes.
            name: Name of the last mapping step (mainly for internal use).
            indent: How of blanks to prepend each line with (mainly for
                internal use).
        """
        strings = []
        ind = " " * indent
        strings.append(ind + f'{name if name else "Step"}:')
        strings.append(
            ind + f"  steptype: " f"{self.steptype.name if self.steptype else None}"
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


def get_nroutes(inputs: "Inputs") -> int:
    """Help function returning the number of routes for an input dict."""
    m = 1
    for input in inputs.values():
        if isinstance(input, MappingStep):
            m *= input.number_of_routes()
    return m


def get_values(
    inputs: "Inputs", routeno: int, quantity: "Any" = Quantity, magnitudes: bool = False
):
    """Help function returning a dict mapping the input names to actual value
    of expected input unit.

    There exists `get_nroutes(inputs)` routes to populate `inputs`.
    `routeno` is the index of the specific route we will use to obtain the
    values.
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
        else:
            values[k] = quantity(v.value, v.unit)

        if magnitudes:
            values = {
                k: v.m if isinstance(v, quantity) else v for k, v in values.items()
            }

    return values


def fno_mapper(triplestore: "Triplestore") -> "Dict[str, list]":
    """Finds all function definitions in `triplestore` based on the function
    ontololy (FNO).

    Return a dict mapping output IRIs to a list of

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
    sources: "Dict[str, Value]",
    triplestore: "Triplestore",
    function_repo: "Any" = None,
    function_mappers: "Sequence[Callable]" = (fno_mapper,),
    default_costs: "Tuple" = (
        ("function", 10.0),
        ("mapsTo", 2.0),
        ("instanceOf", 1.0),
        ("subClassOf", 1.0),
        ("value", 0.0),
    ),
    mapsTo: str = MAP.mapsTo,
    instanceOf: str = DM.instanceOf,
    subClassOf: str = RDFS.subClassOf,
    # description: str = DCTERMS.description,
    label: str = RDFS.label,
    hasUnit: str = DM.hasUnit,
    hasCost: str = DM.hasCost,  # TODO - add hasCost to the DM ontology
) -> MappingStep:
    """Find routes of mappings from any source in `sources` to `target`.

    This implementation supports functions (using FnO) and subclass
    relations.  It also correctly handles transitivity of `mapsTo` and
    `subClassOf` relations.

    Arguments:
        target: IRI of the target in `triplestore`.
        sources: Dict mapping source IRIs to source values.
        triplestore: Triplestore instance.
            It is safe to pass a generator expression too.

    Additional arguments for fine-grained tuning:
        function_repo: Dict mapping function IRIs to corresponding Python
            function.  Default is to use `triplestore.function_repo`.
        function_mappers: Sequence of mapping functions that takes
            `triplestore` as argument and return a dict mapping output IRIs
            to a list of `(function_iri, [input_iris, ...])` tuples.
        default_costs: A dict providing default costs of different types
            of mapping steps ("function", "mapsTo", "instanceOf",
            "subclassOf", and "value").  These costs can be overridden with
            'hasCost' relations in the ontology.
        mapsTo: IRI of 'mapsTo' in `triplestore`.
        instanceOf: IRI of 'instanceOf' in `triplestore`.
        subClassOf: IRI of 'subClassOf' in `triples`.  Set it to None if
            subclasses should not be considered.
        label: IRI of 'label' in `triplestore`.  Used for naming function
            input parameters.  The default is to use rdfs:label.
        hasUnit: IRI of 'hasUnit' in `triples`.  Can be used to explicit
            specify the unit of a quantity.
        hasCost: IRI of 'hasCost' in `triples`.  Used for associating a
            user-defined cost or cost function with instantiation of a
            property.

    Returns:
        A MappingStep instance.  This is a root of a nested tree of
        MappingStep instances providing an (efficient) internal description
        of all possible mapping routes from `sources` to `target`.
    """

    # pylint: disable=too-many-arguments,too-many-locals,too-many-statements

    if function_repo is None:
        function_repo = triplestore.function_repo

    default_costs = dict(default_costs)

    # Create lookup tables for fast access to properties
    # This only transverse `tiples` once
    soMaps = defaultdict(list)  # (s, mapsTo, o)     ==> soMaps[s]  -> [o, ..]
    osMaps = defaultdict(list)  # (o, mapsTo, s)     ==> osMaps[o]  -> [s, ..]
    osSubcl = defaultdict(list)  # (o, subClassOf, s) ==> osSubcl[o] -> [s, ..]
    soInst = {}  # (s, instanceOf, o) ==> soInst[s]  -> o
    osInst = defaultdict(list)  # (o, instanceOf, s) ==> osInst[o]  -> [s, ..]
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

    def getcost(target, stepname):
        """Returns the cost assigned to IRI `target` for a mapping step
        of type `stepname`."""
        cost = soCost.get(target, default_costs[stepname])
        if cost is None:
            return None
        return function_repo[cost] if cost in function_repo else float(cost)

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
            if node in sources:
                value = Value(
                    value=sources[node],
                    unit=soUnit.get(node),
                    iri=node,
                    property_iri=soInst.get(node),
                    cost=getcost(node, "value"),
                )
                step.add_input(value, name=soName.get(node))
            else:
                prevstep = MappingStep(output_iri=node, output_unit=soUnit.get(node))
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
            for func, input_iris in fmap(triplestore)[target]:
                step.steptype = StepType.FUNCTION
                step.cost = getcost(func, "function")
                step.function = function_repo[func]
                step.join_mode = True
                for input_iri in input_iris:
                    step0 = MappingStep(
                        output_iri=input_iri, output_unit=soUnit.get(input_iri)
                    )
                    step.add_input(step0, name=soName.get(input_iri))
                    walk(input_iri, visited, step0)
                step.join_input()

    visited = set()
    step = MappingStep(output_iri=target, output_unit=soUnit.get(target))
    if target in soInst:
        # It is only initially we want to follow instanceOf in forward
        # direction.
        visited.add(target)  # do we really wan't this?
        source = soInst[target]
        step.steptype = StepType.INSTANCEOF
        step.cost = getcost(source, "instanceOf")
        step0 = MappingStep(output_iri=source, output_unit=soUnit.get(source))
        step.add_input(step0, name=soName.get(target))
        step = step0
        target = source
    if target not in soMaps:
        raise MissingRelationError(f'Missing "mapsTo" relation on: {target}')
    walk(target, visited, step)

    return step
