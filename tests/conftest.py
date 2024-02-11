"""Pytest configuration and fixtures."""

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pathlib import Path
    from typing import Any, Callable


@pytest.fixture(scope="session")
def get_ontology_path() -> "Callable[[str], Path]":
    """Return a function to retrieve a Path object to a Turtle file used
    for testing.

    This fixture will be called once during the test session and will then
    be cached.

    Returns:
        A function that can retrieve a Path object to a static ontology test
    file.

    """
    from pathlib import Path

    ontologies_dir = Path(__file__).resolve().parent / "ontologies"

    def _get_ontology_path(ontology_name: str) -> "Path":
        """Return a Path object to at Turtle file used for testing.

        Parameters:
            ontology_name: The ontology file base name to retrieve from the
                list of static ontology test files.


        Returns:
            A `pathlib.Path` instance, representing the ontology test file.

        """
        ontology_path = ontologies_dir / f"{ontology_name}.ttl"
        if ontology_path.exists():
            return ontology_path
        raise ValueError(
            f"{ontology_name}.ttl does not exist in the 'ontologies' test "
            f"folder."
        )

    return _get_ontology_path


@pytest.fixture
def example_function() -> "Callable[[Any, Any], Any]":
    """Return an example function to be used to test the Triplestore.

    Returns:
        A function implementation that can be used with the Triplestore.

    """

    def sum_(first_param: "Any", second_param: "Any") -> "Any":
        """Returns the sum of `first_param` and `second_param`."""
        return first_param + second_param

    return sum_


@pytest.fixture
def expected_function_triplestore(
    example_function: "Callable[[Any, Any], Any]",
) -> str:
    """The expected Turtle-serialized output of a Triplestore.

    Parameters:
        example_function: Pytest fixture found in `conftest.py`.
            This becomes a function implementation that can be used with the
            Triplestore.

    Returns:
        A Turtle-serialized output that would be expected from the Triplestore.

    """
    from tripper.utils import function_id

    fid = function_id(example_function)

    return f"""\
@prefix dcterms: <http://purl.org/dc/terms/> .
@prefix ex: <http://example.com/onto#> .
@prefix fno: <https://w3id.org/function/ontology#> .
@prefix map: <http://emmo.info/domain-mappings#> .
@prefix oteio: <http://emmo.info/oteio#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

ex:sum__{fid} a fno:Function ;
    rdfs:label "sum_"@en ;
    oteio:hasPythonFunctionName "sum_"^^xsd:string ;
    oteio:hasPythonModuleName "conftest"^^xsd:string ;
    dcterms:description "Returns the sum of `first_param` and `second_param`."@en ;
    fno:expects ( ex:sum__{fid}_parameter1_first_param ex:sum__{fid}_parameter2_second_param ) ;
    fno:returns ( ex:sum__{fid}_output1 ) .

<http://onto-ns.com/meta/0.1/MyEntity#myprop> map:mapsTo ex:MyConcept .

ex:AnotherConcept rdfs:subClassOf owl:Thing .

ex:Sum rdfs:subClassOf owl:Thing .

ex:sum__{fid}_output1 a fno:Output ;
    map:mapsTo ex:Sum .

ex:sum__{fid}_parameter1_first_param a fno:Parameter ;
    rdfs:label "first_param"@en ;
    map:mapsTo ex:MyConcept .

ex:sum__{fid}_parameter2_second_param a fno:Parameter ;
    rdfs:label "second_param"@en ;
    map:mapsTo ex:AnotherConcept .

ex:MyConcept rdfs:subClassOf owl:Thing .

"""
