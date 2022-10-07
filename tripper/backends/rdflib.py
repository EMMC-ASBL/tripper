"""Backend for RDFLib."""
# pylint: disable=line-too-long
import warnings
from typing import TYPE_CHECKING

from rdflib import BNode, Graph
from rdflib import Literal as rdflibLiteral
from rdflib import URIRef

from tripper.triplestore import Literal

if TYPE_CHECKING:  # pragma: no cover
    from collections.abc import Sequence
    from typing import Generator, Union

    from tripper.triplestore import Triple


def asuri(value: "Union[None, Literal, str]"):
    """Help function converting a spo-value to proper rdflib type."""
    if value is None:
        return None
    if isinstance(value, Literal):
        return rdflibLiteral(value.value, lang=value.lang, datatype=value.datatype)
    if value.startswith("_:"):
        return BNode(value)
    return URIRef(value)


def astriple(triple: "Triple"):
    """Help function converting a triple to rdflib triple."""
    subject, predicate, object_ = triple
    return asuri(subject), asuri(predicate), asuri(object_)


class RdflibStrategy:
    """Triplestore strategy for rdflib."""

    def __init__(self, **kwargs) -> None:  # pylint: disable=unused-argument
        self.graph = Graph()

    def triples(self, triple: "Triple") -> "Generator":
        """Returns a generator over matching triples."""
        for (
            subject,
            predicate,
            object_,
        ) in self.graph.triples(  # pylint: disable=not-an-iterable
            astriple(triple)
        ):
            yield (
                str(subject),
                str(predicate),
                Literal(object_.value, lang=object_.language, datatype=object_.datatype)
                if isinstance(object_, rdflibLiteral)
                else str(object_),
            )

    def add_triples(self, triples: "Sequence[Triple]"):
        """Add a sequence of triples."""
        for triple in triples:
            self.graph.add(astriple(triple))

    def remove(self, triple: "Triple"):
        """Remove all matching triples from the backend."""
        self.graph.remove(astriple(triple))

    # Optional methods
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
            source=source, location=location, data=data, format=format, **kwargs
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
        result = self.graph.serialize(destination=destination, format=format, **kwargs)
        if destination is None:
            # Depending on the version of rdflib the return value of
            # graph.serialize() man either be a string or a bytes object...
            return result if isinstance(result, str) else result.decode()
        return None

    def query(self, query_object, **kwargs):
        """SPARQL query."""
        # TODO: convert to returned object
        return self.graph.query(query_object=query_object, **kwargs)

    def update(self, update_object, **kwargs):
        """Update triplestore with SPARQL."""
        return self.graph.update(update_object=update_object, **kwargs)

    def bind(self, prefix: str, namespace: str):
        """Bind prefix to namespace.

        Should only be defined if the backend supports namespaces.
        Called by triplestore.bind().
        """
        if namespace:
            self.graph.bind(prefix, namespace, replace=True)
        else:
            warnings.warn("rdflib does not support removing namespace prefixes")

    def namespaces(self) -> dict:
        """Returns a dict mapping prefixes to namespaces.

        Should only be defined if the backend supports namespaces.
        Used by triplestore.parse() to get prefixes after reading
        triples from an external source.
        """
        return {prefix: str(namespace) for prefix, namespace in self.graph.namespaces()}
