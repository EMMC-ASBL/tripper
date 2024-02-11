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
    from typing import Generator, Optional

    from tripper.triplestore import Triple


class ITriplestore(Protocol):
    '''Interface for triplestore backends.

    In addition to the methods specified by this interface, a backend
    may also implement the following optional methods:

    ```python

    def parse(
            self,
            source: Union[str, Path, IO] = None,
            location: str = None,
            data: str = None,
            format: str = None,
            **kwargs
        ):
        """Parse source and add the resulting triples to triplestore.

        The source is specified using one of `source`, `location` or `data`.

        Arguments:
            source: File-like object or file name.
            location: String with relative or absolute URL to source.
            data: String containing the data to be parsed.
            format: Needed if format can not be inferred from source.
            kwargs: Additional backend-specific parameters controlling
                the parsing.
        """

    def serialize(
            self,
            destination: Union[str, Path, IO] = None,
            format: str ='xml',
            **kwargs
        ):
        """Serialise to destination.

        Arguments:
            destination: File name or object to write to.  If None, the
                serialisation is returned.
            format: Format to serialise as.  Supported formats, depends on
                the backend.
            kwargs: Additional backend-specific parameters controlling
                the serialisation.

        Returns:
            Serialised string if `destination` is None.
        """

    def query(self, query_object: str, **kwargs) -> List[Tuple[str, ...]]:
        """SPARQL query.

        Arguments:
            query_object: String with the SPARQL query.
            kwargs: Additional backend-specific keyword arguments.

        Returns:
            List of tuples of IRIs for each matching row.
        """

    def update(self, update_object: str, **kwargs):
        """Update triplestore with SPARQL.

        Arguments:
            query_object: String with the SPARQL query.
            kwargs: Additional backend-specific keyword arguments.

        Note:
            This method is intended for INSERT and DELETE queries.  Use
            the query() method for SELECT queries.
        """

    def bind(self, prefix: str, namespace: str) -> Namespace:
        """Bind prefix to namespace.

        Should only be defined if the backend supports namespaces.
        """

    def namespaces(self) -> dict:
        """Returns a dict mapping prefixes to namespaces.

        Should only be defined if the backend supports namespaces.
        Used by triplestore.parse() to get prefixes after reading
        triples from an external source.
        """

    @classmethod
    def create_database(cls, database: str, **kwargs):
        """Create a new database in backend.

        Parameters:
            database: Name of the new database.
            kwargs: Keyword arguments passed to the backend
                create_database() method.

        Note:
            This is a class method, which operates on the backend
            triplestore without connecting to it.
        """

    @classmethod
    def remove_database(cls, database: str, **kwargs):
        """Remove a database in backend.

        Parameters:
            database: Name of the database to be removed.
            kwargs: Keyword arguments passed to the backend
                remove_database() method.

        Note:
            This is a class method, which operates on the backend
            triplestore without connecting to it.
        """

    @classmethod
    def list_databases(cls, **kwargs):
        """For backends that supports multiple databases, list of all
        databases.

        Parameters:
            kwargs: Keyword arguments passed to the backend
                list_database() method.

        Note:
            This is a class method, which operates on the backend
            triplestore without connecting to it.
        """

    ```
    '''

    def __init__(self, base_iri: "Optional[str]" = None, **kwargs):
        """Initialise triplestore.

        Arguments:
            base_iri: Optional base IRI to initiate the triplestore from.
            kwargs: Additional keyword arguments passed to the backend.
        """

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
