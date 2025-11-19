"""Module providing a simple interface to SPARQL queries.

This module is not imported by default, since it depends on the
excellent `SPARQL-builder` package develop by 7P9 in the PINK project.
"""

from sparqlbuilder import select


def make_query(
    criteria: "Sequence[Tuple]" = (),
    type: "Optional[str]" = None,
    skipblanks: "bool" = True,
    distinct: "bool" = True,
    reduced: "bool" = False,
    limit: "Optional[int]" = None,
    offset: "int" = 0,
    keywords: "Optional[KeywordsType]" = None,
    context: "Optional[ContextType]" = None,
    prefixes: "Optional[dict]" = None,
) -> "str":
    """Creates a SPARQL query to find resources in a knowledge base.

    The returned query will return the IRIs of all resources that match the
    criteria specified in the arguments.

    Arguments:
        criteria: Exact match criteria. A dict of IRI, value pairs, where the
            IRIs refer to data properties on the resource match. The IRIs
            may use any prefix defined in `ts`. E.g. if the prefix `dcterms`
            is in `ts`, it is expanded and the match criteria `dcterms:title`
            is correctly parsed.
        type: Either a [resource type] (ex: "Dataset", "Distribution", ...)
            or the IRI of a class to limit the search to.
        skipblanks: Whether the query will skip matching blank nodes.
        distinct: Whether the query will filter out duplicated matches.
        reduced: A weaker version of `distinct` that may eliminate
            some duplicates but is not required to eliminate all
            duplicates. This can be more efficient than `distinct` in
            some query engines. `distinct` and `reduced` are mutually
            exclusive.
        limit: Limit the number of returned IRIs to this number.
        offset: The index of the first returned IRI. `offset` often used in
            combination with limit for pagination.
        keywords: Keywords instance defining prefixes and keywords for
            use in `criteria`.
        context: Context instance defining prefixes and keywords for
            use in `criteria`.  Extends what has been provided by `keywords`.
        prefixes: Additional prefixes to use in criteria.

    Returns:
        A string with a SPARQL query that can be passed to the
        `Triplestore.query()` method.

    Examples:

        Alternative ways to search for all datasets:

        >>> make_query(criteria=[("rdf:type", "dcat:Dataset")])
        >>> make_query(type="dcat:Dataset"))  # use shorthand `type` argument
        >>> make_query(type="Dataset"))  # refer to a pre-defined keyword

        Search for all datasets created by a given agent:
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


# make_query(prefixes=ts.namespaces)
