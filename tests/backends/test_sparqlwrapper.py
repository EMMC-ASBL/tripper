"""Test SPARQLwrapper backend."""

import pytest


@pytest.mark.network
def test_sparqlwrapper_backend():
    """Test SPARQLwrapper backend."""
    import urllib

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

    # Skip test on failures due to endpoint throttling or access restrictions.
    try:
        res = ts.query(sparql_query)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 429:
            pytest.skip(str(exc))
        else:
            raise
    except urllib.error.HTTPError as exc:
        if exc.code in (403, 429):
            pytest.skip(str(exc))
        else:
            raise
    assert res == [("http://www.wikidata.org/entity/Q20", "Norway")]


def test_backend_sparqlwrapper() -> None:
    """Specifically test the SPARQLWrapper backend Triplestore."""
    import urllib

    from tripper import SKOS, Triplestore
    from tripper.errors import UnknownDatatypeWarning

    SPARQLWrapper = pytest.importorskip("SPARQLWrapper")

    pytest.importorskip("SPARQLWrapper")
    ts = Triplestore(
        backend="sparqlwrapper",
        base_iri="http://vocabs.ardc.edu.au/repository/api/sparql/"
        "csiro_international-chronostratigraphic-chart_geologic-"
        "time-scale-2020",
    )
    with pytest.warns(UnknownDatatypeWarning, match="unknown datatype"):
        try:
            for s, p, o in ts.triples(predicate=SKOS.notation):
                assert s
                assert p
                assert o
        except urllib.error.URLError as exc:
            if "[Errno 110] Connection timed out" in str(exc):
                pytest.skip(str(exc))
            else:
                raise
        except SPARQLWrapper.SPARQLExceptions.EndPointNotFound as exc:
            pytest.skip(str(exc))
