import warnings
from typing import TYPE_CHECKING

from SPARQLWrapper import SPARQLWrapper, GET, POST, JSON, RDFXML

from tripper import Literal

if TYPE_CHECKING:  # pragma: no cover
    from collections.abc import Sequence
    from typing import Generator, Optional

    from triplestore import Triple


class SparqlwrapperStrategy:
    """Triplestore strategy for SPARQLWrapper.

    Arguments:
        base_iri: URI of SPARQL endpoint.
        kwargs: Additional arguments passed to the SPARQLWrapper constructor.
    """

    def __init__(
            self,
            base_iri: str,
            **kwargs
    ):
        self.sparql = SPARQLWrapper(endpoint=base_iri, **kwargs)

    def triples(self, triple: "Triple") -> "Generator":
        """Returns a generator over matching triples."""
        variables = [f"?{v}" for v, t in zip("spo", triple) if t is None]
        where_spec = " ".join(
            f"?{v}" if t is None else t if t.startswith("<") else f"<{t}>"
            for v, t in zip("spo", triple)
        )
        query = "\n".join([
                f"SELECT {' '.join(variables)} WHERE {{",
                f"  {where_spec} .",
                f"}}",
        ])
        self.sparql.setReturnFormat(JSON)
        self.sparql.setMethod(GET)
        self.sparql.setQuery(query)
        ret = self.sparql.queryAndConvert()
        for d in ret['results']['bindings']:
            yield tuple(
                convert_json_entrydict(d[v]) if v in d else t
                for v, t in zip("spo", triple)
            )

    def add_triples(self, triples: "Sequence[Triple]"):
        """Add a sequence of triples."""
        spec = "\n".join(
            "  " + " ".join(
                t.n3() if isinstance(t, Literal) else
                t if t.startswith("<") else
                f"<{t}>"
                for t in triple
            ) + " ."
            for triple in triples
        )
        query = f"INSERT DATA {{\n{spec}\n}}"
        self.sparql.setReturnFormat(RDFXML)
        self.sparql.setMethod(POST)
        self.sparql.setQuery(query)
        return self.sparql.query()

    def remove(self, triple: "Triple"):
        """Remove all matching triples from the backend."""
        spec = " ".join(
            f"?{v}" if t is None else
            t.n3() if isinstance(t, Literal) else
            t if t.startswith("<") else
            f"<{t}>"
            for v, t in zip("spo", triple)
        )
        query = f"DELETE {{ {spec} }}"
        self.sparql.setReturnFormat(RDFXML)
        self.sparql.setMethod(POST)
        self.sparql.setQuery(query)
        return self.sparql.query()



def convert_json_entrydict(entrydict):
    """Convert SPARQLWrapper json entry dict (representing a single IRI or
    literal) to a tripper type."""
    type = entrydict["type"]
    value = entrydict["value"]
    if type == "uri":
        return value
    elif type == "literal":
            return Literal(
                value,
                lang=entrydict.get("xml:lang"),
                datatype=entrydict.get("datatype"),
            )
    elif type == "bnode":
        return value if value.startswith("_:") else f"_:{value}"
    else:
        raise ValueError(f"unexpected type in entrydict: {entrydict}")
