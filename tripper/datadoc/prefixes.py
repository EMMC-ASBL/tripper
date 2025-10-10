"""Utilities for storing and loading namespace prefixes in the triplestore."""

from typing import TYPE_CHECKING

from tripper import OWL, RDF, VANN, XSD, Literal, Triplestore

if TYPE_CHECKING:  # pragma: no cover
    from typing import Iterator, Tuple


_bnode_counter = 0


def bnode() -> str:
    """Returns a new unique blank node."""
    global _bnode_counter  # pylint: disable=global-statement
    _bnode_counter += 1
    return f"_:b{_bnode_counter}"


def save_prefixes(ts: "Triplestore", prefixes: dict) -> None:
    """Save prefixes to the triplestore.

    Prefix-namespace pairs already in the knowledge base will not be
        duplicated.

    Arguments:
        ts: Triplestore instance to store the prefixes to.
        prefixes: Dict to store. It should map prefixes to namespaces.

    """
    existing = set(load_prefixes(ts))
    triples = []
    for k, v in prefixes.items():
        if (k, v) not in existing:
            b = bnode()
            ns = Literal(v, datatype=XSD.anyURI)
            triples.extend(
                [
                    (b, RDF.type, OWL.Ontology),
                    (b, VANN.preferredNamespacePrefix, Literal(k)),
                    (b, VANN.preferredNamespaceUri, ns),
                ]
            )
    ts.add_triples(triples)


def load_prefixes(ts: "Triplestore", prefix=None, namespace=None) -> list:
    """Returns an list of all matching prefix-namespace
    pairs defined in the triplestore.

    Arguments:
        ts: Triplestore instance to load from.
        prefix: prefix to search for
        namespace: namespace to search for (URI)

    Returns:
        List of `(prefix, namespace)` tuples.
    """
    bind = []
    if prefix is not None:
        bind.append(f"BIND({Literal(prefix).n3()} AS ?prefix)")
    if namespace is not None:
        bind.append(
            f"BIND({Literal(namespace, datatype=XSD.anyURI).n3()} AS ?ns)"
        )
    binds = "\n  ".join(bind)
    query = f"""
    SELECT ?prefix ?ns WHERE {{
      {binds}
      ?s <{VANN.preferredNamespacePrefix}> ?prefix ;
         <{VANN.preferredNamespaceUri}> ?ns .
    }}
    """
    return ts.query(query)
