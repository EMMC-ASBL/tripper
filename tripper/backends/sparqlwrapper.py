"""Backend for SPARQLWrapper"""

from typing import TYPE_CHECKING

from tripper import Literal

try:
    from SPARQLWrapper import GET, JSON, POST, RDFXML, SPARQLWrapper
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

    def query(
        self, query_object, **kwargs  # pylint: disable=unused-argument
    ) -> "Union[List[Tuple[str, ...]], bool, Generator[Triple, None, None]]":
        """SPARQL query.

        Parameters:
            query_object: String with the SPARQL query.
            kwargs: Keyword arguments passed to rdflib.Graph.query().

        Returns:
            The return type depends on type of query:
              - SELECT: list of tuples of IRIs for each matching row
              - ASK: TODO
              - CONSTRUCT, DESCRIBE: TODO
        """
        self.sparql.setReturnFormat(JSON)
        self.sparql.setMethod(POST)
        self.sparql.setQuery(query_object)
        ret = self.sparql.queryAndConvert()
        bindings = ret["results"]["bindings"]
        return [
            tuple(str(convert_json_entrydict(v)) for v in row.values())
            for row in bindings
        ]

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
        self.sparql.setReturnFormat(RDFXML)
        self.sparql.setMethod(POST)
        self.sparql.setQuery(query)
        return self.sparql.query()

    def remove(self, triple: "Triple") -> "QueryResult":
        """Remove all matching triples from the backend."""
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
        query = f"DELETE {{ {spec} }}"
        self.sparql.setReturnFormat(RDFXML)
        self.sparql.setMethod(POST)
        self.sparql.setQuery(query)
        return self.sparql.query()


def convert_json_entrydict(entrydict: "Dict[str, str]") -> str:
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
