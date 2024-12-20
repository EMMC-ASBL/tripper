"""Test SPARQLwrapper backend."""

# pylint: disable=invalid-name


def test_sparqlwrapper_backend():
    """Test SPARQLwrapper backend."""
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

    # Ignore failures due to too many requests
    try:
        res = ts.query(sparql_query)
    except requests.HTTPError as exc:
        if "Too Many Requests" not in str(exc):
            raise

    assert res == [("http://www.wikidata.org/entity/Q20", "Norway")]
