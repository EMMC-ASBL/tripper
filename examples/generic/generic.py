"""Test for the generic case described in the README file."""
from tripper import Triplestore
from tripper.mappings import mapping_routes

ts = Triplestore(backend="rdflib")
EX = ts.bind("ex", "http://example.com/generic_example#")
ts.add_function(
    EX.model1,
    expects=EX.model1_input,
    returns=EX.model1_output,
    standard="emmo",
    # standard="fno",
)
ts.add_function(
    EX.model2,
    expects=(EX.model2_input1, EX.model2_input2),
    returns=EX.model2_output,
    standard="emmo",
    # standard="fno",
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
    sources={EX.data1: None, EX.data2: None},
    triplestore=ts,
    # function_mappers = "emmo"
    # function_mappers = "fno"
)

# routes.visualise(0, output="route.svg", format="svg")
