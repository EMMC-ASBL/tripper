"""Workflow example"""

import warnings

from tripper import Triplestore
from tripper.mappings import MappingStep, mapping_routes

warnings.filterwarnings(
    action="ignore",
    message="Function and module name for function '[^']*' is not provided",
    category=UserWarning,
)

ts = Triplestore(backend="rdflib")
EX = ts.bind("ex", "http://example.com/generic_example#")
ts.add_function(
    EX.model1,
    expects=EX.model1_input,
    returns=EX.model1_output,
)
ts.add_function(
    EX.model2,
    expects=(EX.model2_input1, EX.model2_input2),
    returns=EX.model2_output,
)
ts.map(EX.data1, EX.A)
ts.map(EX.model1_input, EX.A)
ts.map(EX.model1_output, EX.B)
ts.map(EX.model2_input1, EX.B)
ts.map(EX.data2, EX.C)
ts.map(EX.model2_input2, EX.C)
ts.map(EX.model2_output, EX.D)
ts.map(EX.target, EX.D)

routes = mapping_routes(
    target=EX.target,
    sources=(EX.data1, EX.data2),
    triplestore=ts,
)

if isinstance(routes, MappingStep):
    print("Number of routes:", routes.number_of_routes())
    routes.visualise(0, output="route.svg", format="svg")
