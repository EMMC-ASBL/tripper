"""Test using SPARQL via Tripper."""

# pylint: disable=invalid-name

import pytest


# if True:
def test_sparql_select():
    """Test SPARQL SELECT query."""
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

    r = list(ts.query(query))

    assert len(r) == 6
    assert len([s for s, p, o in r if p == VCARD.givenName]) == 2
    assert (
        len([s for s, p, o in r if p == VCARD.givenName and o == "Bob"]) == 1
    )
    assert (
        len([s for s, p, o in r if p == VCARD.givenName and o == "Cyril"]) == 0
    )


# if True:
def test_sparql_select2():
    """Test SPARQL SELECT query."""
    # From https://www.w3.org/TR/rdf-sparql-query/#select
    pytest.importorskip("rdflib")
    from textwrap import dedent

    from tripper import Triplestore

    data = dedent(
        """
        @prefix  :  <http://persons.com#> .
        @prefix  foaf:  <http://xmlns.com/foaf/0.1/> .

        :allice    foaf:name   "Alice" .
        :allice    foaf:knows  :bob .
        :allice    foaf:knows  :clare .

        :bob       foaf:name   "Bob" .

        :clare     foaf:name   "Clare" .
        :clare     foaf:nick   "CT" .
        """
    )
    query = dedent(
        """
        PREFIX foaf:    <http://xmlns.com/foaf/0.1/>
        SELECT ?nameX ?nameY ?nickY
        WHERE
          { ?x foaf:knows ?y ;
               foaf:name ?nameX .
            ?y foaf:name ?nameY .
            OPTIONAL { ?y foaf:nick ?nickY }
          }
        """
    )
    ts = Triplestore("rdflib")
    ts.parse(data=data)
    r = ts.query(query)

    assert set(r) == {("Alice", "Bob", "None"), ("Alice", "Clare", "CT")}


# if True:
def test_sparql_construct2():
    """Test SPARQL CONSTRUCT query."""
    # From https://www.w3.org/TR/rdf-sparql-query/#construct
    pytest.importorskip("rdflib")
    from textwrap import dedent

    from tripper import Literal, Triplestore

    # Load pre-inferred EMMO
    ts = Triplestore("rdflib")

    data = dedent(
        """
        @prefix  foaf:  <http://xmlns.com/foaf/0.1/> .

        _:a    foaf:name   "Alice" .
        _:a    foaf:mbox   <mailto:alice@example.org> .
        """
    )
    query = dedent(
        """
        PREFIX foaf:    <http://xmlns.com/foaf/0.1/>
        PREFIX vcard:   <http://www.w3.org/2001/vcard-rdf/3.0#>
        CONSTRUCT   { <http://example.org/person#Alice> vcard:FN ?name }
        WHERE       { ?x foaf:name ?name }
        """
    )
    ts = Triplestore("rdflib")
    ts.parse(data=data)
    r = ts.query(query)

    assert set(r) == {
        (
            "http://example.org/person#Alice",
            "http://www.w3.org/2001/vcard-rdf/3.0#FN",
            Literal("Alice"),
        )
    }


# if True:
def test_sparql_ask():
    """Test SPARQL ASK query."""
    # From https://www.w3.org/TR/rdf-sparql-query/#ask
    pytest.importorskip("rdflib")
    from textwrap import dedent

    from tripper import Triplestore

    # Load pre-inferred EMMO
    ts = Triplestore("rdflib")

    data = dedent(
        """
        @prefix foaf:       <http://xmlns.com/foaf/0.1/> .

        _:a  foaf:name       "Alice" .
        _:a  foaf:homepage   <http://work.example.org/alice/> .

        _:b  foaf:name       "Bob" .
        _:b  foaf:mbox       <mailto:bob@work.example> .
        """
    )
    query = dedent(
        """
        PREFIX foaf:    <http://xmlns.com/foaf/0.1/>
        ASK  { ?x foaf:name  "Alice" }
        """
    )
    ts = Triplestore("rdflib")
    ts.parse(data=data)
    r = ts.query(query)
    assert r is True


# if True:
def test_sparql_describe():
    """Test SPARQL DESCRIBE query."""
    # From https://www.w3.org/TR/rdf-sparql-query/#describe
    pytest.importorskip("rdflib")
    from textwrap import dedent

    from tripper import Literal, Triplestore

    # Load pre-inferred EMMO
    ts = Triplestore("rdflib")

    data = dedent(
        """
        @prefix foaf:   <http://xmlns.com/foaf/0.1/> .
        @prefix vcard:  <http://www.w3.org/2001/vcard-rdf/3.0> .
        @prefix exOrg:  <http://org.example.com/employees#> .
        @prefix rdf:    <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
        @prefix owl:    <http://www.w3.org/2002/07/owl#> .

        exOrg:Allice
            exOrg:employeeId    "1234" ;
            foaf:mbox_sha1sum   "ABCD1234" .

        foaf:mbox_sha1sum  rdf:type  owl:InverseFunctionalProperty .
        """
    )
    query = dedent(
        """
        PREFIX foaf:   <http://xmlns.com/foaf/0.1/>
        DESCRIBE ?x
        WHERE    { ?x foaf:mbox_sha1sum "ABCD1234" }
        """
    )
    ts = Triplestore("rdflib")
    ts.parse(data=data)
    r = ts.query(query)

    assert set(r) == set(
        [
            (
                "http://org.example.com/employees#Allice",
                "http://xmlns.com/foaf/0.1/mbox_sha1sum",
                Literal("ABCD1234"),
            ),
            (
                "http://org.example.com/employees#Allice",
                "http://org.example.com/employees#employeeId",
                Literal("1234"),
            ),
        ]
    )
