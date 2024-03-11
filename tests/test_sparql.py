"""Test using SPARQL via Tripper."""

# pylint: disable=invalid-name

from tripper import Triplestore


# if True:
def test_sparql():
    """Test SPARQL query."""
    # Load pre-inferred EMMO
    ts = Triplestore("rdflib", base_iri="https://w3id.org/emmo#")
    ts.parse("https://w3id.org/emmo#inferred")

    # Bind "emmo" prefix to base_iri
    EMMO = ts.bind("emmo", label_annotations=True, check=True)

    # Get IRI and symbol of all length units
    query = f"""
    PREFIX owl:  <http://www.w3.org/2002/07/owl#>
    PREFIX rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

    SELECT ?unit ?symbol
    WHERE {{
      ?unit rdfs:subClassOf <{EMMO.LengthUnit}> .
      ?unit rdfs:subClassOf ?r .
      ?r rdf:type owl:Restriction .
      ?r owl:onProperty <{EMMO.hasSymbolValue}> .
      ?r owl:hasValue ?symbol .
    }}
    """
    r = ts.query(query)
    assert (EMMO.Metre, "m") in r
    assert (EMMO.AstronomicalUnit, "au") in r
