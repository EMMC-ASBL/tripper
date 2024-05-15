"""Test using SPARQL via Tripper."""

# pylint: disable=invalid-name

import pytest


# if True:
def test_sparql():
    """Test SPARQL query."""
    pytest.importorskip("rdflib")
    from tripper import Triplestore

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


# if True:
def test_sparql_construct():
    """Test SPARQL construct query."""
    pytest.importorskip("rdflib")
    from textwrap import dedent

    from tripper import Triplestore

    data = dedent(
        """
        @prefix  foaf:  <http://xmlns.com/foaf/0.1/> .

        _:a foaf:givenname   "Alice" .
        _:a foaf:family_name "Hacker" .
        _:b foaf:firstname   "Bob" .
        _:b foaf:surname     "Hacker" .
        """
    )
    query = dedent(
        """
        PREFIX foaf:    <http://xmlns.com/foaf/0.1/>
        PREFIX vcard:   <http://www.w3.org/2001/vcard-rdf/3.0#>

        CONSTRUCT {
          ?x  vcard:N _:v .
          _:v vcard:givenName ?gname .
          _:v vcard:familyName ?fname
        }
        WHERE {
          { ?x foaf:firstname ?gname } UNION  { ?x foaf:givenname   ?gname } .
          { ?x foaf:surname   ?fname } UNION  { ?x foaf:family_name ?fname } .
        }
        """
    )
    ts = Triplestore("rdflib")
    ts.parse(data=data)
    VCARD = ts.bind("vcard", "http://www.w3.org/2001/vcard-rdf/3.0#")

    r = ts.query(query)

    assert len(r) == 6
    assert len([s for s, p, o in r if p == VCARD.givenName]) == 2
    assert (
        len([s for s, p, o in r if p == VCARD.givenName and o == "Bob"]) == 1
    )
    assert (
        len([s for s, p, o in r if p == VCARD.givenName and o == "Cyril"]) == 0
    )
