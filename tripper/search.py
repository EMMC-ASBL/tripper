"""Module providing a simple interface to SPARQL queries.

This module is not imported by default, since it depends on the
excellent `SPARQL-builder` package develop by 7P9 in the PINK project.
"""
from sparqlbuilder import select


def make_query(
    criteria: "Optional[Union[Sequence[Tuple[str, str]], Mapping]]" = None,
    prefixes: "Optional[dict]" = None,
    type: = None,
    regex: "Optional[dict]" = None,
    flags: "Optional[str]" = None,
    keywords: "Optional[Keywords]" = None,
    query_type: "Optional[str]" = "SELECT DISTINCT",
    limit: "Optional[int]" = None,
    offset: "Optional[int]" = None,
) -> "str":
"""


Examples:

    Alternative ways to search for all datasets:

    >>> make_query(criteria=[("rdf:type", "dcat:Dataset")])
    >>> make_query(criteria=[("rdf:type", "Dataset")])
    >>> make_query(type="dcat:Dataset"))
    >>> make_query(type="Dataset"))

    All datasets created by a given agent:
    >>> make_query(
    ...     type="Dataset",
    ...     criteria=[("creator", "kb:JohnDow")],
    ... )

    alternatively:

    >>> make_query(
    ...     criteria=[("rdf:type": "Dataset"), ("creator", "kb:JohnDow")],
    ... )

    All datasets that has a creator, regardless who:
    >>> make_query(
    ...     type="Dataset",
    ...     criteria=[("creator", None)],
    ... )

"""


make_query(prefixes=ts.namespaces)
