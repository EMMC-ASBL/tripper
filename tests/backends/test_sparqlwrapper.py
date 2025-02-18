"""Test SPARQLwrapper backend."""

# pylint: disable=invalid-name


def test_sparqlwrapper_backend():
    """Test SPARQLwrapper backend."""
    import urllib

    import pytest

    pytest.importorskip("SPARQLWrapper")
    requests = pytest.importorskip("requests")

    from tripper import Triplestore

    # Requires internet connection to connect to wikidata
    sparql_query = """
#Country where the capital is Oslo.
SELECT DISTINCT ?country ?countryLabel
WHERE
{
  ?country wdt:P31 wd:Q3624078 . # isA country
  ?country wdt:P36 wd:Q585 . # captial Oslo
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en" }
}
"""

    endpoint_url = "https://query.wikidata.org/sparql"
    ts = Triplestore(backend="sparqlwrapper", base_iri=endpoint_url)

    # Skip test on failures due to too many requests or 403 response
    try:
        res = ts.query(sparql_query)
    except requests.HTTPError as exc:
        if "Too Many Requests" in str(exc):
            pytest.skip(str(exc))
        else:
            raise
    except urllib.error.HTTPError as exc:
        if "HTTP Error 403: Forbidden" in str(exc):
            pytest.skip(str(exc))
        elif "Too Many Requests" in str(exc):
            pytest.skip(str(exc))
        else:
            raise
    assert res == [("http://www.wikidata.org/entity/Q20", "Norway")]
