"""Backend for RDFLib.

For developers: The usage of `s`, `p`, and `o` represent the different parts of
an RDF Triple: subject, predicate, and object.
"""

# pylint: disable=line-too-long
import warnings
from typing import TYPE_CHECKING, Generator

try:
    import rdflib  # pylint: disable=unused-import
except ImportError as exc:
    raise ImportError(
        "rdflib is not installed.\nInstall it with:\n\n    pip install rdflib"
    ) from exc

from rdflib import BNode, Graph
from rdflib import Literal as rdflibLiteral
from rdflib import URIRef
from rdflib.util import guess_format

from tripper import Literal
from tripper.errors import UnusedArgumentWarning
from tripper.utils import parse_literal

if TYPE_CHECKING:  # pragma: no cover
    from collections.abc import Sequence
    from typing import List, Optional, Tuple, Union

    from tripper.triplestore import Triple


def asuri(value: "Union[None, Literal, str]"):
    """Help function converting a spo-value to proper rdflib type."""
    if value is None:
        return None
    if isinstance(value, Literal):
        return rdflibLiteral(
            value.value, lang=value.lang, datatype=value.datatype
        )
    if value.startswith("_:"):
        return BNode(value[2:])
    return URIRef(value)


def astriple(triple: "Triple"):
    """Help function converting a triple to rdflib triple."""
    s, p, o = triple
    return asuri(s), asuri(p), asuri(o)


class RdflibStrategy:
    """Triplestore strategy for rdflib.

    Arguments:
        base_iri: Unused by the rdflib backend.  The `base_iri` argument is
            still used for encapsulating the Triplestore class.
        database: Unused - rdflib does not support multiple databases.
        triplestore_url: If given, initialise the triplestore from this
            storage.  When `close()` is called, the storage will be
            overwritten with the current content of the triplestore.
        format: Format of storage specified with `base_iri`.
        graph: A rdflib.Graph instance to expose with tripper, instead of
            creating a new empty Graph object.
    """

    def __init__(
        self,
        base_iri: "Optional[str]" = None,  # pylint: disable=unused-argument
        database: "Optional[str]" = None,
        triplestore_url: "Optional[str]" = None,
        format: "Optional[str]" = None,  # pylint: disable=redefined-builtin
        graph: "Optional[Graph]" = None,
    ) -> None:
        # Note that although `base_iri` is unused in this backend, it may
        # still be used by calling Triplestore object.
        if database:
            warnings.warn("database", UnusedArgumentWarning, stacklevel=3)

        self.graph = graph if graph else Graph()
        self.triplestore_url = triplestore_url
        if self.triplestore_url is not None:
            if format is None:
                format = guess_format(self.triplestore_url)
            self.parse(location=self.triplestore_url, format=format)
        self.base_format = format

    def triples(self, triple: "Triple") -> "Generator[Triple, None, None]":
        """Returns a generator over matching triples."""
        return _convert_triples_to_tripper(
            self.graph.triples(astriple(triple))
        )

    def add_triples(self, triples: "Sequence[Triple]"):
        """Add a sequence of triples."""
        for triple in triples:
            self.graph.add(astriple(triple))

    def remove(self, triple: "Triple"):
        """Remove all matching triples from the backend."""
        self.graph.remove(astriple(triple))

    # Optional methods
    def close(self):
        """Close the internal RDFLib graph."""
        if self.triplestore_url:
            self.serialize(
                destination=self.triplestore_url, format=self.base_format
            )
        self.graph.close()

    def parse(
        self,
        source=None,
        location=None,
        data=None,
        format=None,  # pylint: disable=redefined-builtin
        **kwargs,
    ):
        """Parse source and add the resulting triples to triplestore.

        The source is specified using one of `source`, `location` or `data`.

        Parameters:
            source: File-like object or file name.
            location: String with relative or absolute URL to source.
            data: String containing the data to be parsed.
            format: Needed if format can not be inferred from source.
            kwargs: Additional less used keyword arguments.
                See https://rdflib.readthedocs.io/en/stable/apidocs/rdflib.html#rdflib.Graph.parse
        """
        self.graph.parse(
            source=source,
            location=location,
            data=data,
            format=format,
            **kwargs,
        )

    def serialize(
        self,
        destination=None,
        format="turtle",  # pylint: disable=redefined-builtin
        **kwargs,
    ) -> "Union[None, str]":
        """Serialise to destination.

        Parameters:
            destination: File name or object to write to. If None, the serialisation is
                returned.
            format: Format to serialise as. Supported formats, depends on the backend.
            kwargs: Passed to the rdflib.Graph.serialize() method.
                See https://rdflib.readthedocs.io/en/stable/apidocs/rdflib.html#rdflib.Graph.serialize

        Returns:
            Serialised string if `destination` is None.
        """
        result = self.graph.serialize(
            destination=destination, format=format, **kwargs
        )
        if destination is None:
            # Depending on the version of rdflib the return value of
            # graph.serialize() man either be a string or a bytes object...
            return result if isinstance(result, str) else result.decode()
        return None

    def query(
        self, query_object, **kwargs
    ) -> "Union[List[Tuple[str, ...]], bool, Generator[Triple, None, None]]":
        """SPARQL query.

        Parameters:
            query_object: String with the SPARQL query.
            kwargs: Keyword arguments passed to rdflib.Graph.query().

        Returns:
            The return type depends on type of query:
              - SELECT: list of tuples of IRIs for each matching row
              - ASK: bool
              - CONSTRUCT, DESCRIBE: generator over triples

            For more info, see
            https://rdflib.readthedocs.io/en/stable/apidocs/rdflib.html#rdflib.query.Result
        """
        result = self.graph.query(query_object=query_object, **kwargs)

        # The type of the result object depends not only on the type of query,
        # but also on the version of rdflib...  We try to be general here.
        if hasattr(result, "type"):
            resulttype = result.type
        elif result.__class__.__name__ == "ResultRow":
            resulttype = "SELECT"
        elif isinstance(result, bool):
            resulttype = "ASK"
        elif isinstance(result, Generator):
            resulttype = "CONSTRUCT"  # also DESCRIBE
        else:
            warnings.warn(
                "Unknown return type from rdflib.query(). Return it unprocessed."
            )
            return result  # type: ignore

        if resulttype == "SELECT":
            return [tuple(str(v) for v in row) for row in result]  # type: ignore
        if resulttype == "ASK":
            return bool(result)
        if resulttype in ("CONSTRUCT", "DESCRIBE"):
            return _convert_triples_to_tripper(result)
        assert False, "should never be reached"  # nosec

    def update(self, update_object, **kwargs) -> None:
        """Update triplestore with SPARQL.

        Parameters:
            update_object: String with the SPARQL query.
            kwargs: Keyword arguments passed to rdflib.Graph.update().

        Note:
            This method is intended for INSERT and DELETE queries. Use
            the query() method for SELECT queries.

        """
        return self.graph.update(update_object=update_object, **kwargs)

    def bind(self, prefix: str, namespace: str):
        """Bind prefix to namespace.

        Should only be defined if the backend supports namespaces.
        Called by triplestore.bind().
        """
        if namespace:
            self.graph.bind(prefix, namespace, replace=True)
        else:
            warnings.warn(
                "rdflib does not support removing namespace prefixes"
            )

    def namespaces(self) -> dict:
        """Returns a dict mapping prefixes to namespaces.

        Should only be defined if the backend supports namespaces.
        Used by triplestore.parse() to get prefixes after reading
        triples from an external source.
        """
        return {
            prefix: str(namespace)
            for prefix, namespace in self.graph.namespaces()
        }


def _convert_triples_to_tripper(triples) -> "Generator[Triple, None, None]":
    """Help function that converts a iterator/generator of rdflib triples
    to tripper triples."""
    for s, p, o in triples:  ### p ylint: disable=not-an-iterable
        yield (
            (
                f"_:{s}"
                if isinstance(s, BNode) and not s.startswith("_:")
                else str(s)
            ),
            str(p),
            (
                parse_literal(o)
                if isinstance(o, rdflibLiteral)
                else (
                    f"_:{o}"
                    if isinstance(o, BNode) and not o.startswith("_:")
                    else str(o)
                )
            ),
        )
