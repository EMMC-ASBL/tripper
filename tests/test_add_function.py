"""Test Triplestore.add_function()"""

# pylint: disable=invalid-name


def test_add_function():
    """Test add_function()"""
    import pytest

    pytest.importorskip("rdflib")
    from tripper import Triplestore
    from tripper.utils import function_id

    def func(a, b):
        """Returns the sum of `a` and `b`."""
        return a + b

    f_id = function_id(func)

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
        == f"""
@prefix dcterms: <http://purl.org/dc/terms/> .
@prefix ex: <http://example.com/ex#> .
@prefix fno: <https://w3id.org/function/ontology#> .
@prefix map: <http://emmo.info/domain-mappings#> .
@prefix oteio: <http://emmo.info/oteio#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

<:func_{f_id}> a fno:Function ;
    rdfs:label "func"@en ;
    oteio:hasPythonFunctionName "func"^^xsd:string ;
    oteio:hasPythonModuleName "{__name__}"^^xsd:string ;
    dcterms:description "Returns the sum of `a` and `b`."@en ;
    fno:expects ( <:func_{f_id}_parameter1_a> <:func_{f_id}_parameter2_b> ) ;
    fno:returns ( <:func_{f_id}_output1> ) .

<:func_{f_id}_output1> a fno:Output ;
    map:mapsTo ex:sum .

<:func_{f_id}_parameter1_a> a fno:Parameter ;
    rdfs:label "a"@en ;
    map:mapsTo ex:arg1 .

<:func_{f_id}_parameter2_b> a fno:Parameter ;
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
        == f"""
@prefix dcterms: <http://purl.org/dc/terms/> .
@prefix emmo: <http://emmo.info/emmo#> .
@prefix ex: <http://example.com/ex#> .
@prefix oteio: <http://emmo.info/oteio#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

<:func_{f_id}> a emmo:EMMO_4299e344_a321_4ef2_a744_bacfcce80afc ;
    rdfs:label "func"@en ;
    emmo:EMMO_36e69413_8c59_4799_946c_10b05d266e22 ex:arg1,
        ex:arg2 ;
    emmo:EMMO_c4bace1d_4db0_4cd3_87e9_18122bae2840 ex:sum ;
    oteio:hasPythonFunctionName "func"^^xsd:string ;
    oteio:hasPythonModuleName "{__name__}"^^xsd:string ;
    dcterms:description "Returns the sum of `a` and `b`."@en .

ex:arg1 a emmo:EMMO_194e367c_9783_4bf5_96d0_9ad597d48d9a ;
    rdfs:label "a"@en .

ex:arg2 a emmo:EMMO_194e367c_9783_4bf5_96d0_9ad597d48d9a ;
    rdfs:label "b"@en .

ex:sum a emmo:EMMO_194e367c_9783_4bf5_96d0_9ad597d48d9a .
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
        == f"""
@prefix dcterms: <http://purl.org/dc/terms/> .
@prefix emmo: <http://emmo.info/emmo#> .
@prefix ex: <http://example.com/ex#> .
@prefix oteio: <http://emmo.info/oteio#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

<:func_{f_id}> a emmo:EMMO_4299e344_a321_4ef2_a744_bacfcce80afc ;
    rdfs:label "func"@en ;
    emmo:EMMO_36e69413_8c59_4799_946c_10b05d266e22 ex:arg1,
        ex:arg2 ;
    emmo:EMMO_c4bace1d_4db0_4cd3_87e9_18122bae2840 ex:sum ;
    oteio:hasPythonFunctionName "func"^^xsd:string ;
    oteio:hasPythonModuleName "{__name__}"^^xsd:string ;
    dcterms:description "Returns the sum of `a` and `b`."@en .

ex:arg1 a emmo:EMMO_194e367c_9783_4bf5_96d0_9ad597d48d9a ;
    rdfs:label "x"@en .

ex:arg2 a emmo:EMMO_194e367c_9783_4bf5_96d0_9ad597d48d9a ;
    rdfs:label "y"@en .

ex:sum a emmo:EMMO_194e367c_9783_4bf5_96d0_9ad597d48d9a .
""".strip()
    )
