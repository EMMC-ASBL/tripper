"""Backend for EMMOntoPy.

For developers: The usage of `s`, `p`, and `o` represent the different parts of
an RDF Triple: subject, predicate, and object.
"""

# pylint: disable=protected-access
import os
import tempfile
from typing import TYPE_CHECKING

from tripper.literal import Literal

try:
    from ontopy.ontology import Ontology, _unabbreviate, get_ontology
except ImportError as exc:
    raise ImportError(
        "EMMOntoPy is not installed.\nInstall it with:\n\n"
        "    pip install EMMOntoPy"
    ) from exc

if TYPE_CHECKING:  # pragma: no cover
    from collections.abc import Sequence
    from typing import Generator, List, Optional, Union

    from rdflib.query import Result

    from tripper.triplestore import Triple


class OntopyStrategy:
    """Triplestore strategy for EMMOntoPy.

    Arguments:
        base_iri: The base iri of the ontology.
            Default to "http://example.com/onto#" if `onto` is not given.
        database: Unused - ontopy does not support multiple databases.
        onto: Ontology to initiate the triplestore from.  Defaults to an new
            ontology with the given `base_iri`.
        load: Whether to load the ontology.
        kwargs: Keyword arguments passed to the ontology load() method.

    Either the `base_iri` or `onto` argument must be provided.
    """

    def __init__(
        self,
        base_iri: "Optional[str]" = None,
        database: "Optional[str]" = None,
        onto: "Optional[Ontology]" = None,
        load: bool = False,
        **kwargs,
    ):
        # pylint: disable=unused-argument
        if onto is None:
            if base_iri is None:
                base_iri = "http://example.com/onto#"
            self.onto = get_ontology(base_iri)
        elif isinstance(onto, Ontology):
            self.onto = onto
        else:
            raise TypeError("`onto` must be either an ontology or None")

        if load:
            self.onto.load(**kwargs)

    def triples(self, triple: "Triple") -> "Generator[Triple, None, None]":
        """Returns a generator over matching triples."""

        def to_literal(o, datatype) -> Literal:
            """Returns a literal from (o, datatype)."""
            if isinstance(datatype, str) and datatype.startswith("@"):
                return Literal(o, lang=datatype[1:], datatype=None)
            return Literal(o, lang=None, datatype=datatype)

        s, p, o = triple
        abb = (
            None if (s) is None else self.onto._abbreviate(s),
            None if (p) is None else self.onto._abbreviate(p),
            None if (o) is None else self.onto._abbreviate(o),
        )
        for s, p, o in self.onto._get_obj_triples_spo_spo(*abb):
            yield (
                _unabbreviate(self.onto, s),
                _unabbreviate(self.onto, p),
                _unabbreviate(self.onto, o),
            )
        for s, p, o, datatype in self.onto._get_data_triples_spod_spod(
            *abb, d=""
        ):
            yield (
                _unabbreviate(self.onto, s),
                _unabbreviate(self.onto, p),
                to_literal(o, datatype),
            )

    def add_triples(self, triples: "Sequence[Triple]"):
        """Add a sequence of triples."""
        if TYPE_CHECKING:  # pragma: no cover
            datatype: "Union[int, str]"
        for s, p, o in triples:
            if isinstance(o, Literal):
                if o.lang:
                    datatype = f"@{o.lang}"
                elif o.datatype:
                    datatype = f"^^{o.datatype}"
                else:
                    datatype = 0
                self.onto._add_data_triple_spod(
                    self.onto._abbreviate(s),
                    self.onto._abbreviate(p),
                    self.onto._abbreviate(o),
                    datatype,
                )
            else:
                self.onto._add_obj_triple_spo(
                    self.onto._abbreviate(s),
                    self.onto._abbreviate(p),
                    self.onto._abbreviate(o),
                )

    def remove(self, triple: "Triple"):
        """Remove all matching triples from the backend."""
        s, p, o = triple
        to_remove = list(
            self.onto._get_triples_spod_spod(
                self.onto._abbreviate(s) if (s) is not None else None,
                self.onto._abbreviate(p) if (s) is not None else None,
                self.onto._abbreviate(o) if (s) is not None else None,
            )
        )
        for s, p, o, datatype in to_remove:
            if datatype:
                self.onto._del_data_triple_spod(s, p, o, datatype)
            else:
                self.onto._del_obj_triple_spo(s, p, o)

    # Optional methods
    def parse(
        self,
        source=None,
        location=None,
        data=None,
        format=None,  # pylint: disable=redefined-builtin
        encoding=None,
        **kwargs,
    ):
        """Parse source and add the resulting triples to triplestore.

        The source is specified using one of `source`, `location` or `data`.

        Parameters:
            source: File-like object or file name.
            location: String with relative or absolute URL to source.
            data: String containing the data to be parsed.
            format: Needed if format can not be inferred from source.
            encoding: Encoding argument to io.open().
            kwargs: Additional keyword arguments passed to Ontology.load().
        """
        if source:
            self.onto.load(filename=source, format=format, **kwargs)
        elif location:
            self.onto.load(filename=location, format=format, **kwargs)
        elif data:
            # s = io.StringIO(data)
            # self.onto.load(filename=s, format=format, **kwargs)

            # Could have been done much nicer if it hasn't been for Windows
            filename = None
            try:
                tmpfile_options = {"delete": False}
                if isinstance(data, str):
                    tmpfile_options.update(mode="w+t", encoding=encoding)
                with tempfile.NamedTemporaryFile(**tmpfile_options) as handle:
                    handle.write(data)
                    filename = handle.name
                self.onto.load(filename=filename, format=format, **kwargs)
            finally:
                if filename:
                    os.remove(filename)

        else:
            raise ValueError(
                "either `source`, `location` or `data` must be given"
            )

    def serialize(
        self,
        destination=None,
        format="turtle",  # pylint: disable=redefined-builtin
        **kwargs,
    ) -> "Union[None, str]":
        """Serialise to destination.

        Parameters:
            destination: File name or object to write to.  If None, the
                serialisation is returned.
            format: Format to serialise as.  Supported formats, depends on
                the backend.
            kwargs: Passed to the Ontology.save() method.

        Returns:
            Serialised string if `destination` is None.
        """
        if destination:
            self.onto.save(destination, format=format, **kwargs)
        else:
            # Clumsy implementation due to Windows file locking...
            filename = None
            try:
                with tempfile.NamedTemporaryFile(delete=False) as handle:
                    filename = handle.name
                    self.onto.save(filename, format=format, **kwargs)
                with open(filename, "rt", encoding="utf8") as handle:
                    return handle.read()
            finally:
                if filename:
                    os.remove(filename)
        return None

    def query(
        self, query_object, native=True, **kwargs
    ) -> "Union[List, Result]":
        """SPARQL query.

        Parameters:
            query_object: String with the SPARQL query.
            native: Whether or not to use EMMOntoPy/Owlready2 or RDFLib.
            kwargs: Keyword arguments passed to rdflib.Graph.query().

        Returns:
            SPARQL query results.

        """
        if TYPE_CHECKING:  # pragma: no cover
            res: "Union[List, Result]"

        if native:
            res = self.onto.world.sparql(query_object)
        else:
            graph = self.onto.world.as_rdflib_graph()
            res = graph.query(query_object, **kwargs)
        # TODO: Convert result to expected type
        return res

    def update(self, update_object, native=True, **kwargs) -> None:
        """Update triplestore with SPARQL.

        Parameters:
            update_object: String with the SPARQL query.
            native: Whether or not to use EMMOntoPy/Owlready2 or RDFLib.
            kwargs: Keyword arguments passed to rdflib.Graph.update().

        Note:
            This method is intended for INSERT and DELETE queries. Use
            the query() method for SELECT queries.

        """
        if native:
            self.onto.world.sparql(update_object)
        else:
            graph = self.onto.world.as_rdflib_graph()
            graph.update(update_object, **kwargs)
