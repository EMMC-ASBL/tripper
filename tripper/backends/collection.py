"""Backend for DLite collections.

"""
# pylint: disable=protected-access,invalid-name
from typing import TYPE_CHECKING

from tripper.literal import Literal
from tripper.utils import parse_object

try:
    import dlite
except ImportError as exc:
    raise ImportError(
        "DLite is not installed.\nInstall it with:\n\n"
        "    pip install DLite-Python"
    ) from exc

if TYPE_CHECKING:  # pragma: no cover
    from collections.abc import Sequence
    from typing import Generator, List, Optional, Union

    from tripper.triplestore import Triple


class CollectionStrategy:
    """Triplestore strategy for DLite collections.

    Arguments:
        base_iri: Unused.
        database: Unused - collection does not support multiple databases.
        collection: Optional collection from which to initialise the
            triplestore from.
    """

    def __init__(
        self,
        base_iri: "Optional[str]" = None,
        database: "Optional[str]" = None,
        collection: "Optional[Union[dlite.Collection, str]]" = None,
    ):
        # pylint: disable=unused-argument
        if collection is None:
            self.collection = dlite.Collection()
        elif isinstance(collection, str):
            self.collection = dlite.get_instance(collection)
            if self.collection.meta.uri != dlite.COLLECTION_ENTITY:
                raise TypeError(
                    f"expected '{collection}' to be a collection, was a "
                    f"{self.collection.meta.uri}"
                )
        elif isinstance(collection, dlite.Collection):
            self.collection = collection
        else:
            raise TypeError(
                "`collection` should be None, string or a collection"
            )

    def triples(self, triple: "Triple") -> "Generator[Triple, None, None]":
        """Returns a generator over matching triples."""
        for s, p, o, d in self.collection.get_relations(*triple, rettype="T"):
            if d:
                lang = d[1:] if d[0] == "@" else None
                dt = None if lang else d
                yield s, p, Literal(o, lang=lang, datatype=dt)
            else:
                yield s, p, o

    def add_triples(self, triples: "Sequence[Triple]"):
        """Add a sequence of triples."""
        for s, p, o in triples:
            # Strange complains by mypy - it assumed that
            # parse_object() is returning a `str` regardless that it
            # has been declared to return the union of `str` and
            # `Literal`.
            v = parse_object(o)
            o = v if isinstance(v, str) else v.value  # type: ignore
            d = (
                None
                if not isinstance(v, Literal)
                else f"@{v.lang}"
                if v.lang
                else v.datatype
            )
            self.collection.add_relation(s, p, o, d)

    def remove(self, triple: "Triple"):
        """Remove all matching triples from the backend."""
        s, p, o = triple
        v = parse_object(o)
        o = v if isinstance(v, str) else v.value  # type: ignore
        d = (
            None
            if isinstance(v, str)
            else f"@{v.lang}"  # type: ignore
            if v.lang  # type: ignore
            else v.datatype  # type: ignore
        )
        # v_str = v.n3() if isinstance(v, Literal) else v
        self.collection.remove_relations(s, p, o, d)
