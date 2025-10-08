"""Test the datadoc.prefixes module."""

if True:
    # def test_prefixes():
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
        "dcat": "http://www.w3.org/ns/dcat#",
        "dcterms": "http://purl.org/dc/terms/",
        "dctype": "http://purl.org/dc/dcmitype/",
        "eli": "http://data.europa.eu/eli/ontology#",
        "foaf": "http://xmlns.com/foaf/0.1/",
        "iana": "https://www.iana.org/assignments/media-types/",
        "locn": "http://www.w3.org/ns/locn#",
        "odrl": "http://www.w3.org/ns/odrl/2/",
        "owl": "http://www.w3.org/2002/07/owl#",
        "prov": "http://www.w3.org/ns/prov#",
        "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    }
    intersection = {
        k: prefixes1[k] for k in set(prefixes1).intersection(prefixes2)
    }

    ts = Triplestore(backend="rdflib")

    r1 = save_prefixes(ts, prefixes1)
    assert not r1

    r2 = load_prefixes(ts)
    assert dict(r2) == prefixes1

    d3 = save_prefixes(ts, prefixes2)
    assert d3 == intersection
