"""Backend for SPARQLWrapper"""

import re
from typing import TYPE_CHECKING

from rdflib import Graph

from tripper import Literal
from tripper.backends.rdflib import _convert_triples_to_tripper
from tripper.errors import TripperError

try:
    from SPARQLWrapper import GET, JSON, POST, TURTLE, SPARQLWrapper
except ImportError as exc:
    raise ImportError(
        "SPARQLWrapper is not installed.\nInstall it with:\n\n"
        "    pip install SPARQLWrapper"
    ) from exc

if TYPE_CHECKING:  # pragma: no cover
    from collections.abc import Sequence
    from typing import Dict, Generator, List, Optional, Tuple, Union

    from SPARQLWrapper import QueryResult
    from triplestore import Triple


class SparqlwrapperStrategy:
    """Triplestore strategy for SPARQLWrapper.

    Arguments:
        base_iri: SPARQL endpoint.
        update_iri: Update SPARQL endpoint. For some triplestores (e.g.
                    GraphDB), update endpoint is different from base endpoint.
        username: User name.
        password: Password.
        kwargs: Additional arguments passed to the SPARQLWrapper constructor.

    """

    prefer_sparql = True

    def __init__(
        self,
        base_iri: str,
        update_iri: "Optional[str]" = None,
        username: "Optional[str]" = None,
        password: "Optional[str]" = None,
        **kwargs,
    ) -> None:
        kwargs.pop(
            "database", None
        )  # database is not used in the SPARQLWrapper backend
        self.sparql = SPARQLWrapper(
            endpoint=base_iri, updateEndpoint=update_iri, **kwargs
        )
        if username and password:
            self.sparql.setCredentials(username, password)

        self.update_iri = update_iri

    @property
    def update_iri(self) -> "Optional[str]":
        """Getter for the update IRI."""
        return self._update_iri

    @update_iri.setter
    def update_iri(self, new_update_iri: "Optional[str]") -> None:
        """Setter for the update IRI that also updates the SPARQL endpoint."""
        self._update_iri = new_update_iri
        # Update the SPARQLWrapper's updateEndpoint only if it was initialized.
        if hasattr(self, "sparql"):
            self.sparql.updateEndpoint = new_update_iri

    def query(
        self,
        query_object: str,
        **kwargs,  # pylint: disable=unused-argument
    ) -> "Union[List[Tuple[str, ...]], bool, Generator[Triple, None, None]]":
        """SPARQL query.

        Parameters:
            query_object: String with the SPARQL query.
            kwargs: Keyword arguments passed to rdflib.Graph.query().

        Returns:
            The return type depends on type of query:
              - ASK: whether there is a match
              - CONSTRUCT: generator over triples
              - DESCRIBE: generator over triples
              - SELECT: list of tuples of IRIs
        """
        query_type = self._get_sparql_query_type(query_object)

        if query_type == "ASK":
            self.sparql.setReturnFormat(JSON)
            self.sparql.setMethod(POST)
            self.sparql.setQuery(query_object)
            result = self.sparql.queryAndConvert()
            value = result["boolean"]
            return value

        if query_type == "CONSTRUCT":
            self.sparql.setReturnFormat(TURTLE)
            self.sparql.setMethod(POST)
            self.sparql.setQuery(query_object)
            results = self.sparql.queryAndConvert()
            graph = Graph()
            graph.parse(data=results.decode("utf-8"), format="turtle")
            return _convert_triples_to_tripper(graph)

        if query_type == "DESCRIBE":
            self.sparql.setReturnFormat(TURTLE)
            self.sparql.setMethod(POST)
            self.sparql.setQuery(query_object)
            results = self.sparql.queryAndConvert()
            graph = Graph()
            graph.parse(data=results.decode("utf-8"), format="turtle")
            return _convert_triples_to_tripper(graph)

        if query_type == "SELECT":
            self.sparql.setReturnFormat(JSON)
            self.sparql.setMethod(POST)
            self.sparql.setQuery(query_object)
            ret = self.sparql.queryAndConvert()
            bindings = ret["results"]["bindings"]
            return [
                tuple(convert_json_entrydict(v) for v in row.values())
                for row in bindings
            ]

        raise NotImplementedError(
            f"Query type '{query_type}' not implemented."
        )

    def _get_sparql_query_type(self, query: str) -> str:
        """
        Returns the SPARQL query type (e.g., SELECT, ASK, CONSTRUCT, DESCRIBE)
        by finding the first word of a sentence that matches one of these
        keywords.
        If none is found, it returns 'UNKNOWN'.
        """
        # A regex that looks for a sentence start:
        # either the beginning of the string or following a newline
        # or a period. It then matches one of the keywords.
        pattern = re.compile(
            r"(?:(?<=^)|(?<=[\.\n]))\s*(ASK|CONSTRUCT|SELECT|DESCRIBE|"
            r"DELETE|INSERT)\b",
            re.IGNORECASE,
        )
        match = pattern.search(query)
        if match:
            return match.group(1).upper()
        return "UNKNOWN"

    def update(
        self,
        update_object: str,
        **kwargs,  # pylint: disable=unused-argument
    ) -> None:
        """Update triplestore with SPARQL query.

        Arguments:
            update_object: String with the SPARQL query.
            kwargs: Additional backend-specific keyword arguments.

        Note:
            This method is intended for INSERT and DELETE queries.  Use
            the query() method for ASK/CONSTRUCT/SELECT/DESCRIBE queries.
        """
        query_type = self._get_sparql_query_type(update_object)
        if query_type not in ("DELETE", "INSERT"):
            raise NotImplementedError(
                f"Update query type '{query_type}' not implemented."
            )
        self.sparql.setMethod(POST)
        self.sparql.setQuery(update_object)
        self.sparql.query()

    def triples(self, triple: "Triple") -> "Generator[Triple, None, None]":
        """Returns a generator over matching triples."""
        variables = [
            f"?{triple_name}"
            for triple_name, triple_value in zip("spo", triple)
            if triple_value is None
        ]
        where_spec = " ".join(
            (
                f"?{triple_name}"
                if triple_value is None
                else (
                    triple_value
                    if triple_value.startswith("<")
                    else f"<{triple_value}>"
                )
            )
            for triple_name, triple_value in zip("spo", triple)
        )
        query = "\n".join(
            [
                f"SELECT {' '.join(variables)} WHERE {{",
                f"  {where_spec} .",
                "}",
            ]
        )
        self.sparql.setReturnFormat(JSON)
        self.sparql.setMethod(GET)
        self.sparql.setQuery(query)
        ret = self.sparql.queryAndConvert()
        for binding in ret["results"]["bindings"]:
            yield tuple(
                (
                    convert_json_entrydict(binding[name])
                    if name in binding
                    else value
                )
                for name, value in zip("spo", triple)
            )

    def add_triples(self, triples: "Sequence[Triple]") -> "QueryResult":
        """Add a sequence of triples."""

        self._check_endpoint()

        spec = "\n".join(
            "  "
            + " ".join(
                (
                    value.n3()
                    if isinstance(value, Literal)
                    else value if value.startswith("<") else f"<{value}>"
                )
                for value in triple
            )
            + " ."
            for triple in triples
        )
        query = f"INSERT DATA {{\n{spec}\n}}"

        self.sparql.setReturnFormat(TURTLE)
        self.sparql.setMethod(POST)
        self.sparql.setQuery(query)
        return self.sparql.query()

    def remove(self, triple: "Triple") -> "QueryResult":
        """Remove all matching triples from the backend."""
        self._check_endpoint()
        spec = " ".join(
            (
                f"?{name}"
                if value is None
                else (
                    value.n3()
                    if isinstance(value, Literal)
                    else value if value.startswith("<") else f"<{value}>"
                )
            )
            for name, value in zip("spo", triple)
        )
        query = f"""
        DELETE WHERE {{
          {spec} .
        }}
        """

        self.sparql.setReturnFormat(TURTLE)
        self.sparql.setMethod(POST)
        self.sparql.setQuery(query)
        return self.sparql.query()

    def _check_endpoint(self):
        """Check if the update endpoint is valid"""
        if not self.sparql.isSparqlUpdateRequest() and self.update_iri is None:
            raise TripperError(
                f"The base_iri '{self.sparql.updateEndpoint}' "
                "is not a valid update endpoint. "
                "For updates it is necessary to give the "
                "'update_iri' as argument to the triplestore directly,"
                "or update it with ts.backend.update_iri = ..."
            )


def convert_json_entrydict(entrydict: dict) -> str:
    """Convert SPARQLWrapper json entry dict (representing a single IRI or
    literal) to a tripper type."""
    if entrydict["type"] == "uri":
        return entrydict["value"]
    if entrydict["type"] == "literal":
        return Literal(
            entrydict["value"],
            lang=entrydict.get("xml:lang"),
            datatype=entrydict.get("datatype"),
        )
    if entrydict["type"] == "bnode":
        return (
            entrydict["value"]
            if entrydict["value"].startswith("_:")
            else f"_:{entrydict['value']}"
        )

    raise ValueError(f"unexpected type in entrydict: {entrydict}")
