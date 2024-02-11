"""Backend for RDFLib.

For developers: The usage of `s`, `p`, and `o` represent the different parts of
an RDF Triple: subject, predicate, and object.
"""

# pylint: disable=line-too-long
import warnings
from typing import TYPE_CHECKING

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
    from typing import Generator, List, Optional, Tuple, Union

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
        return BNode(value)
    return URIRef(value)


def astriple(triple: "Triple"):
    """Help function converting a triple to rdflib triple."""
    s, p, o = triple
    return asuri(s), asuri(p), asuri(o)


class RdflibStrategy:
    """Triplestore strategy for rdflib.

    Arguments:
        base_iri: Unused by this backend.
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
        base_iri: "Optional[str]" = None,
        database: "Optional[str]" = None,
        triplestore_url: "Optional[str]" = None,
        format: "Optional[str]" = None,  # pylint: disable=redefined-builtin
        graph: "Graph" = None,
    ) -> None:
        if base_iri:
            warnings.warn("base_iri", UnusedArgumentWarning, stacklevel=3)
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
        for s, p, o in self.graph.triples(  # pylint: disable=not-an-iterable
            astriple(triple)
        ):
            yield (
                str(s),
                str(p),
                parse_literal(o) if isinstance(o, rdflibLiteral) else str(o),
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

    def query(self, query_object, **kwargs) -> "List[Tuple[str, ...]]":
        """SPARQL query.

        Parameters:
            query_object: String with the SPARQL query.
            kwargs: Keyword arguments passed to rdflib.Graph.query().

        Returns:
            List of tuples of IRIs for each matching row.

        """
        rows = self.graph.query(query_object=query_object, **kwargs)
        return [tuple(str(v) for v in row) for row in rows]

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
