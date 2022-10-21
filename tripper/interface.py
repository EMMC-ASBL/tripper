"""Provides the ITriplestore protocol class, that documents the interface
of the triplestore backends."""
import sys
from typing import TYPE_CHECKING

if sys.version_info < (3, 8):
    from typing_extensions import Protocol
else:
    from typing import Protocol

if TYPE_CHECKING:  # pragma: no cover
    from collections.abc import Sequence
    from typing import Generator

    from tripper.triplestore import Triple


class ITriplestore(Protocol):
    '''Interface for triplestore backends.

    In addition to the methods specified by this interface, a backend
    may also implement the following optional methods:

    ```python

    def __init__(self, base_iri=None, **kwargs)

    def parse(self, source=None, location=None, data=None, format=None,
              **kwargs):
        """Parse source and add the resulting triples to triplestore.

        The source is specified using one of `source`, `location` or `data`.

        Parameters:
            source: File-like object or file name.
            location: String with relative or absolute URL to source.
            data: String containing the data to be parsed.
            format: Needed if format can not be inferred from source.
            kwargs: Additional backend-specific parameters controlling
                the parsing.
        """

    def serialize(self, destination=None, format='xml', **kwargs)
        """Serialise to destination.

        Parameters:
            destination: File name or object to write to.  If None, the
                serialisation is returned.
            format: Format to serialise as.  Supported formats, depends on
                the backend.
            kwargs: Additional backend-specific parameters controlling
                the serialisation.

        Returns:
            Serialised string if `destination` is None.
        """

    def query(self, query_object, **kwargs):
        """SPARQL query.

        Parameters:
            query_object: String with the SPARQL query.
            kwargs: Additional backend-specific keyword arguments.

        Returns:
            List of tuples of IRIs for each matching row.
        """

    def update(self, update_object, **kwargs):
        """Update triplestore with SPARQL.

        Parameters:
            query_object: String with the SPARQL query.
            kwargs: Additional backend-specific keyword arguments.

        Note:
            This method is intended for INSERT and DELETE queries.  Use
            the query() method for SELECT queries.
        """

    def bind(self, prefix: str, namespace: str):
        """Bind prefix to namespace.

        Should only be defined if the backend supports namespaces.
        """

    def namespaces(self) -> dict
        """Returns a dict mapping prefixes to namespaces.

        Should only be defined if the backend supports namespaces.
        Used by triplestore.parse() to get prefixes after reading
        triples from an external source.
        """
    ```
    '''

    def triples(self, triple: "Triple") -> "Generator":
        """Returns a generator over matching triples.

        Arguments:
            triple: A `(s, p, o)` tuple where `s`, `p` and `o` should
                either be None (matching anything) or an exact IRI to
                match.
        """

    def add_triples(self, triples: "Sequence[Triple]"):
        """Add a sequence of triples.

        Arguments:
            triples: A sequence of `(s, p, o)` tuples to add to the
                triplestore.
        """

    def remove(self, triple: "Triple"):
        """Remove all matching triples from the backend."""
