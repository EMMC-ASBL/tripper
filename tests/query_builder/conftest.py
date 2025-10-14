"""Pytest configuration and fixtures for query_builder tests."""

import pytest


@pytest.fixture
def in_memory_store():
    """Provides an in-memory Tripper Triplestore for SPARQL query testing."""
    from tripper import Triplestore

    ts = Triplestore("rdflib")
    ts.parse(data="""
        @prefix foaf: <http://xmlns.com/foaf/0.1/> .
        @prefix ex: <http://example.org/> .

        # Researchers
        ex:alice a ex:Researcher ;
            foaf:name "Alice" ;
            foaf:mbox <mailto:alice@example.org> ;
            ex:affiliation ex:university1 ;
            ex:specialization ex:QuantumPhysics ;
            foaf:knows ex:bob .

        ex:bob a ex:Researcher ;
            foaf:name "Bob" ;
            foaf:mbox <mailto:bob@example.org> ;
            ex:affiliation ex:university2 ;
            ex:specialization ex:MaterialsScience .

        ex:charlie a ex:Researcher ;
            foaf:name "Charlie" ;
            ex:affiliation ex:institute1 ;
            ex:specialization ex:QuantumPhysics .

        # Research Papers
        ex:paper1 a ex:ResearchPaper ;
            ex:title "Quantum Computing Advances" ;
            ex:author ex:alice ;
            ex:field ex:QuantumPhysics ;
            ex:citationCount 150 ;
            ex:publishedYear 2023 ;
            ex:publishedIn ex:journal1 .

        ex:paper2 a ex:ResearchPaper ;
            ex:title "Quantum Algorithms for Optimization" ;
            ex:author ex:alice ;
            ex:field ex:QuantumPhysics ;
            ex:citationCount 89 ;
            ex:publishedYear 2024 ;
            ex:publishedIn ex:journal1 .

        ex:paper3 a ex:ResearchPaper ;
            ex:title "Novel Superconducting Materials" ;
            ex:author ex:bob ;
            ex:field ex:MaterialsScience ;
            ex:citationCount 203 ;
            ex:publishedYear 2023 ;
            ex:publishedIn ex:journal2 .

        ex:paper4 a ex:ResearchPaper ;
            ex:title "Quantum Error Correction Methods" ;
            ex:author ex:charlie ;
            ex:field ex:QuantumPhysics ;
            ex:citationCount 95 ;
            ex:publishedYear 2024 ;
            ex:publishedIn ex:journal1 .

        # Institutions
        ex:university1 a ex:University ;
            ex:name "Nordfjord University of Technology" ;
            ex:location "Bergstad" ;
            ex:shortName "NUT" .

        ex:university2 a ex:University ;
            ex:name "Fjellby Institute" ;
            ex:location "Skoghavn" ;
            ex:shortName "FI" .

        ex:institute1 a ex:ResearchInstitute ;
            ex:name "Nordic Advanced Research Center" ;
            ex:location "Bergstad" ;
            ex:type "Independent Research Institute" .

        # Journals
        ex:journal1 a ex:Journal ;
            ex:name "Northern European Quantum Review" ;
            ex:impactFactor 8.5 .

        ex:journal2 a ex:Journal ;
            ex:name "Scandinavian Materials Quarterly" ;
            ex:impactFactor 7.2 .
    """, format="turtle")

    return ts
