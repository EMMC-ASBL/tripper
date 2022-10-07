"""Backend for EMMOntoPy."""
# pylint: disable=protected-access
import os
import tempfile
from typing import TYPE_CHECKING

from ontopy.ontology import Ontology, _unabbreviate, get_ontology

from tripper.triplestore import Literal

if TYPE_CHECKING:  # pragma: no cover
    from collections.abc import Sequence
    from typing import Generator, Optional, Union

    from tripper.triplestore import Triple


class OntopyStrategy:
    """Triplestore strategy for EMMOntoPy.

    Arguments:
        base_iri: The base iri of the ontology.
            Default to "http://example.com/onto#" if `onto` is not given.
        onto: Ontology to initiate the triplestore from.  Defaults to an new
            ontology with the given `base_iri`.
        load: Whether to load the ontology.
        kwargs: Keyword arguments passed to the ontology load() method.

    Either the `base_iri` or `onto` argument must be provided.
    """

    def __init__(
        self,
        base_iri: "Optional[str]" = None,
        onto: "Optional[Ontology]" = None,
        load: bool = False,
        **kwargs,
    ):
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

    def triples(self, triple: "Triple") -> "Generator":
        """Returns a generator over matching triples."""

        def to_literal(object_, datum):
            """Returns a literal from (object_, datum)."""
            if isinstance(datum, str) and datum.startswith("@"):
                lang, datatype = datum[1:], None
            else:
                lang, datatype = None, datum
            return Literal(object_, lang=lang, datatype=datatype)

        subject, predicate, object_ = triple
        abb = (
            None if (subject) is None else self.onto._abbreviate(subject),
            None if (predicate) is None else self.onto._abbreviate(predicate),
            None if (object_) is None else self.onto._abbreviate(object_),
        )
        for subject, predicate, object_ in self.onto._get_obj_triples_spo_spo(*abb):
            yield (
                _unabbreviate(self.onto, subject),
                _unabbreviate(self.onto, predicate),
                _unabbreviate(self.onto, object_),
            )
        for subject, predicate, object_, datum in self.onto._get_data_triples_spod_spod(
            *abb, d=""
        ):
            yield (
                _unabbreviate(self.onto, subject),
                _unabbreviate(self.onto, predicate),
                to_literal(object_, datum),
            )

    def add_triples(self, triples: "Sequence[Triple]"):
        """Add a sequence of triples."""
        if TYPE_CHECKING:  # pragma: no cover
            datum: "Union[int, str]"
        for subject, predicate, object_ in triples:
            if isinstance(object_, Literal):
                if object_.lang:
                    datum = f"@{object_.lang}"
                elif object_.datatype:
                    datum = f"^^{object_.datatype}"
                else:
                    datum = 0
                self.onto._add_data_triple_spod(
                    self.onto._abbreviate(subject),
                    self.onto._abbreviate(predicate),
                    self.onto._abbreviate(object_),
                    datum,
                )
            else:
                self.onto._add_obj_triple_spo(
                    self.onto._abbreviate(subject),
                    self.onto._abbreviate(predicate),
                    self.onto._abbreviate(object_),
                )

    def remove(self, triple: "Triple"):
        """Remove all matching triples from the backend."""
        subject, predicate, object_ = triple
        to_remove = list(
            self.onto._get_triples_spod_spod(
                self.onto._abbreviate(subject) if (subject) is not None else None,
                self.onto._abbreviate(predicate) if (subject) is not None else None,
                self.onto._abbreviate(object_) if (subject) is not None else None,
            )
        )
        for subject, predicate, object_, datum in to_remove:
            if datum:
                self.onto._del_data_triple_spod(subject, predicate, object_, datum)
            else:
                self.onto._del_obj_triple_spo(subject, predicate, object_)

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
            raise ValueError("either `source`, `location` or `data` must be given")

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

    def query(self, query_object, native=True, **kwargs):
        """SPARQL query."""
        if native:
            res = self.onto.world.sparql(query_object)
        else:
            graph = self.onto.world.as_rdflib_graph()
            res = graph.query(query_object, **kwargs)
        # TODO: Convert result to expected type
        return res

    def update(self, update_object, native=True, **kwargs):
        """Update triplestore with SPARQL."""
        if native:
            self.onto.world.sparql(update_object)
        else:
            graph = self.onto.world.as_rdflib_graph()
            graph.update(update_object, **kwargs)
