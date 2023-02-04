from tripper import Namespace, Triplestore
from tripper.mappings import mapping_routes

EX = Namespace("http://example.com/generic_example#")

ts = Triplestore(backend="rdflib")
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
# ts.map(EX.data1, EX.A)
# ts.map(EX.model1_input, EX.A)
# ts.map(EX.model1_output, EX.B)
# ts.map(EX.model2_input1, EX.B)
# ts.map(EX.data2, EX.C)
# ts.map(EX.model2_input2, EX.C)
# ts.map(EX.model2_output, EX.D)
# ts.map(EX.target, EX.D)

ts.add_mapsTo(EX.A, EX.data1)
ts.add_mapsTo(EX.A, EX.model1_input)
ts.add_mapsTo(EX.B, EX.model1_output)
ts.add_mapsTo(EX.B, EX.model2_input1)
ts.add_mapsTo(EX.C, EX.data2)
ts.add_mapsTo(EX.C, EX.model2_input2)
ts.add_mapsTo(EX.D, EX.model2_output)
ts.add_mapsTo(EX.D, EX.target)

routes = mapping_routes(
    target=EX.target,
    sources=(EX.data1, EX.data2),
    triplestore=ts,
)

print("Number of routes:", routes.number_of_routes())
print(routes.show())
