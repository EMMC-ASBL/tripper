"""Test the datadoc.prefixes module."""

import pytest

pytest.importorskip("pyld")
pytest.importorskip("rdflib")


def test_prefixes():
    """Test load_prefixes() and save_prefixes()."""
    from tripper import Triplestore
    from tripper.datadoc.prefixes import load_prefixes, save_prefixes

    prefixes1 = {
        "adms": "http://www.w3.org/ns/adms#",
        "dcat": "http://www.w3.org/ns/dcat#",
        "dcatap": "http://data.europa.eu/r5r/",
        "dcterms": "http://purl.org/dc/terms/",
        "dctype": "http://purl.org/dc/dcmitype/",
        "eli": "http://data.europa.eu/eli/ontology#",
    }
    prefixes2 = {
        "dcat": "http://www.w3.org/ns/dcat#",  # overlap with prefixes1
        "dcterms": "http://purl.org/dc/terms/",  # overlap with prefixes1
        "dctype": "http://purl.org/dc/dcmitype/",  # overlap with prefixes1
        "eli": "http://data.europa.eu/eli/ontology#",  # overlap with prefixes1
        "foaf": "http://xmlns.com/foaf/0.1/",
        "iana": "https://www.iana.org/assignments/media-types/",
        "locn": "http://www.w3.org/ns/locn#",
        "odrl": "http://www.w3.org/ns/odrl/2/",
        "owl": "http://www.w3.org/2002/07/owl#",
        "prov": "http://www.w3.org/ns/prov#",
        "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    }
    prefixes3 = {
        "dct": "http://purl.org/dc/terms/",
        "dcat": "http://example.org/ns/dcat/",
    }

    ts = Triplestore(backend="rdflib")

    r1 = load_prefixes(ts)
    assert not r1

    save_prefixes(ts, prefixes1)
    r2 = load_prefixes(ts)
    assert set(r2) == set(prefixes1.items())

    save_prefixes(ts, prefixes2)
    r3 = load_prefixes(ts)
    assert set(r3) == set(prefixes1.items()).union(prefixes2.items())

    save_prefixes(ts, prefixes3)
    r4 = load_prefixes(ts)
    assert set(r4) == set(prefixes1.items()).union(prefixes2.items()).union(
        prefixes3.items()
    )

    save_prefixes(ts, prefixes3)  # Save the same prefixes twice
    r5 = load_prefixes(ts)
    assert set(r5) == set(r4)

    r6 = load_prefixes(ts, prefix="owl")
    assert r6 == [("owl", prefixes2["owl"])]

    r7 = load_prefixes(ts, prefix="dcat")
    assert set(r7) == {
        ("dcat", prefixes2["dcat"]),
        ("dcat", prefixes3["dcat"]),
    }

    r8 = load_prefixes(ts, namespace=prefixes1["adms"])
    assert r8 == [("adms", prefixes1["adms"])]

    r9 = load_prefixes(ts, namespace=prefixes3["dct"])
    assert set(r9) == {
        ("dcterms", prefixes1["dcterms"]),
        ("dct", prefixes3["dct"]),
    }
