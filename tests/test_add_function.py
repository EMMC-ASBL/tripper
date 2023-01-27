"""Test Triplestore.add_function()"""
# pylint: disable=invalid-name
from tripper import Triplestore


def func(a, b):
    """Returns the sum of `a` and `b`."""
    return a + b


ts = Triplestore(backend="rdflib")
EX = ts.bind("ex", "http://example.com/ex#")
ts.add_function(
    func,
    expects=[EX.arg1, EX.arg2],
    returns=EX.sum,
    standard="fno",
)
assert (
    ts.serialize().strip()
    == """
@prefix dcterms: <http://purl.org/dc/terms/> .
@prefix ex: <http://example.com/ex#> .
@prefix fno: <https://w3id.org/function/ontology#> .
@prefix map: <http://emmo.info/domain-mappings#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

<:func_f1a5429a> a fno:Function ;
    dcterms:description "Returns the sum of `a` and `b`."@en ;
    fno:expects ( <:func_f1a5429a_parameter1_a> <:func_f1a5429a_parameter2_b> ) ;
    fno:returns ( <:func_f1a5429a_output1> ) .

<:func_f1a5429a_output1> a fno:Output ;
    map:mapsTo ex:sum .

<:func_f1a5429a_parameter1_a> a fno:Parameter ;
    rdfs:label "a"@en ;
    map:mapsTo ex:arg1 .

<:func_f1a5429a_parameter2_b> a fno:Parameter ;
    rdfs:label "b"@en ;
    map:mapsTo ex:arg2 .
""".strip()
)


ts2 = Triplestore(backend="rdflib")
EX = ts2.bind("ex", "http://example.com/ex#")
ts2.add_function(
    func,
    expects=[EX.arg1, EX.arg2],
    returns=EX.sum,
    standard="emmo",
)
assert (
    ts2.serialize().strip()
    == """
@prefix dcterms: <http://purl.org/dc/terms/> .
@prefix emmo: <http://emmo.info/emmo#> .
@prefix ex: <http://example.com/ex#> .
@prefix map: <http://emmo.info/domain-mappings#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

<:func_f1a5429a> a emmo:EMMO_4299e344_a321_4ef2_a744_bacfcce80afc ;
    emmo:EMMO_36e69413_8c59_4799_946c_10b05d266e22 <:func_f1a5429a_input_a>,
        <:func_f1a5429a_input_b> ;
    emmo:EMMO_c4bace1d_4db0_4cd3_87e9_18122bae2840 <:func_f1a5429a_output1> ;
    dcterms:description "Returns the sum of `a` and `b`."@en .

<:func_f1a5429a_input_a> a emmo:EMMO_194e367c_9783_4bf5_96d0_9ad597d48d9a ;
    rdfs:label "a"@en ;
    map:mapsTo ex:arg1 .

<:func_f1a5429a_input_b> a emmo:EMMO_194e367c_9783_4bf5_96d0_9ad597d48d9a ;
    rdfs:label "b"@en ;
    map:mapsTo ex:arg2 .

<:func_f1a5429a_output1> a emmo:EMMO_194e367c_9783_4bf5_96d0_9ad597d48d9a ;
    map:mapsTo ex:sum .
""".strip()
)


ts3 = Triplestore(backend="rdflib")
EX = ts3.bind("ex", "http://example.com/ex#")
ts3.add_function(
    func,
    expects={"x": EX.arg1, "y": EX.arg2},
    returns=EX.sum,
    standard="emmo",
)
assert (
    ts3.serialize().strip()
    == """
@prefix dcterms: <http://purl.org/dc/terms/> .
@prefix emmo: <http://emmo.info/emmo#> .
@prefix ex: <http://example.com/ex#> .
@prefix map: <http://emmo.info/domain-mappings#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

<:func_f1a5429a> a emmo:EMMO_4299e344_a321_4ef2_a744_bacfcce80afc ;
    emmo:EMMO_36e69413_8c59_4799_946c_10b05d266e22 <:func_f1a5429a_input_x>,
        <:func_f1a5429a_input_y> ;
    emmo:EMMO_c4bace1d_4db0_4cd3_87e9_18122bae2840 <:func_f1a5429a_output1> ;
    dcterms:description "Returns the sum of `a` and `b`."@en .

<:func_f1a5429a_input_x> a emmo:EMMO_194e367c_9783_4bf5_96d0_9ad597d48d9a ;
    rdfs:label "x"@en ;
    map:mapsTo ex:arg1 .

<:func_f1a5429a_input_y> a emmo:EMMO_194e367c_9783_4bf5_96d0_9ad597d48d9a ;
    rdfs:label "y"@en ;
    map:mapsTo ex:arg2 .

<:func_f1a5429a_output1> a emmo:EMMO_194e367c_9783_4bf5_96d0_9ad597d48d9a ;
    map:mapsTo ex:sum .
""".strip()
)