"""Utilities for storing and loading namespace prefixes in the triplestore."""

from typing import TYPE_CHECKING

from tripper import OWL, RDF, VANN, XSD, Literal, Triplestore

if TYPE_CHECKING:  # pragma: no cover
    from typing import Iterator, Tuple


def save_prefixes(ts: "Triplestore", prefixes: dict) -> dict:
    """Save prefixes to the triplestore.

    Prefixes already in the knowledge base will not be saved. Instead they
    will returned in a dict, that maps the existing prefixes to the existing
    namespaces.

    Arguments:
        ts: Triplestore instance to store the prefixes to.
        prefixes: Dict to store. It should map prefixes to namespaces.

    Returns:
        dict mapping prefixes already in the triplestore to the namespace
        defined in the triplestore.
    """
    existing = dict(load_prefixes(ts))
    n = 0  # blank node counter
    d = {}  # returned dict
    triples = []
    for k, v in prefixes.items():
        if k in existing:
            d[k] = existing[k]
        else:
            triples.extend(
                [
                    (f"_:b{n}", RDF.type, OWL.Ontology),
                    (f"_:b{n}", VANN.preferredNamespacePrefix, Literal(k)),
                    (
                        f"_:b{n}",
                        VANN.preferredNamespaceUri,
                        Literal(v, datatype=XSD.anyURI),
                    ),
                ]
            )
            n += 1
            ts.add_triples(triples)
    return d


def load_prefixes(ts: "Triplestore", prefix=None, namespace=None) -> list:
    """Return an list over all iterator over all matching prefix-namespace
    pairs defined in the triplestore.

    Arguments:
        ts: Triplestore instance to load from.
        prefix:
        namespace:

    Returns:
        Iterator over `(prefix, namespace)` tuples.
    """
    query = f"""
    SELECT ?prefix ?ns WHERE {{
        ?s <{VANN.preferredNamespacePrefix}> ?prefix ;
           <{VANN.preferredNamespaceUri}> ?ns .
    }}
    """
    return ts.query(query)
