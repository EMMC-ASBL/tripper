"""
SPARQL Query Builder

Main query builder class with fluent interface for constructing SPARQL queries.
"""

from typing import Any, Callable, Dict, List, Optional, Union

from .elements import (
    SPARQLElement,
    TripleElement,
    OptionalBlock,
    UnionBlock,
    MinusBlock,
    FilterElement,
    GraphBlock,
)
from .formatter import (
    sanitize_uri,
    sanitize_variable,
    format_literal,
    escape_string,
)


class SPARQLQuery:
    """Main query builder class with fluent interface"""

    def __init__(self):
        self._prefixes: Dict[str, str] = {}
        self._variables: List[str] = []
        self._distinct = False
        self._reduced = False
        self._patterns: List[SPARQLElement] = []
        self._order_by: List[tuple] = []
        self._group_by: List[str] = []
        self._having_conditions: List[str] = []
        self._limit_value: Optional[int] = None
        self._offset_value: Optional[int] = None
        self._from_graphs: List[str] = []
        self._from_named_graphs: List[str] = []

        # Context stack for nested patterns
        self._context_stack: List[List[SPARQLElement]] = [self._patterns]

    def prefix(self, prefix: str, uri: str) -> 'SPARQLQuery':
        """Add a prefix declaration to the SPARQL query.

        This method registers a namespace prefix that can be used to abbreviate URIs
        in the SPARQL query.

        Args:
            prefix (str): The namespace prefix (e.g., 'foaf', 'rdf', 'rdfs')
            uri (str): The full URI for the namespace (e.g., 'http://xmlns.com/foaf/0.1/')

        Returns:
            SPARQLQuery: Amended query instance to allow method chaining.

        Example:
            >>> query.prefix('foaf', 'http://xmlns.com/foaf/0.1/')
            >>> query.prefix('ex', 'http://example.org/')
        """
        sanitized_uri = sanitize_uri(uri)
        self._prefixes[prefix] = sanitized_uri
        return self

    def select(self, *variables: str) -> 'SPARQLQuery':
        """
        Specify variables to select in the SPARQL query.

        This method adds variables to the SELECT clause of the SPARQL query being built.

        Args:
            *variables (str): Variable names to select in the SPARQL query. Variables
                must include the '?' or '$' prefix (e.g., '?name', '?age').
                If no variables are provided, the query will select all variables (SELECT *).

        Returns:
            SPARQLQuery: Amended query instance to allow method chaining.

        Examples:
            >>> query.select('?name', '?age', '?email')
            SELECT ?name ?age ?email

            >>> query.select()
            SELECT *
        """
        for var in variables:
            sanitized_var = sanitize_variable(var)
            self._variables.append(sanitized_var)
        return self

    def select_distinct(self, *variables: str) -> 'SPARQLQuery':
        """SELECT DISTINCT query that removes duplicate results from the result set.

        Args:
            *variables (str): Variable names to select in the SPARQL query. Variables
                must include the '?' or '$' prefix (e.g., '?name', '?age').
                If no variables are provided, the query will select all variables (SELECT *).

        Returns:
            SPARQLQuery: Amended query instance to allow method chaining.

        Raises:
            ValueError: If REDUCED is already set (DISTINCT and REDUCED are mutually exclusive).

        Examples:
            >>> query.select_distinct("?name", "?age")
            SELECT DISTINCT ?name ?age

            >>> query.select_distinct()
            SELECT DISTINCT *
        """
        if self._reduced:
            raise ValueError("Cannot use both DISTINCT and REDUCED in the same query")
        self._distinct = True
        return self.select(*variables)

    def select_reduced(self, *variables: str) -> 'SPARQLQuery':
        """SELECT REDUCED query that eliminates duplicate solutions while allowing some duplicates to remain.

        REDUCED is a weaker version of DISTINCT that may eliminate some duplicates but is not required
        to eliminate all duplicates. This can be more efficient than DISTINCT in some query engines.

        Args:
            *variables (str): Variable names to select in the SPARQL query. Variables
                must include the '?' or '$' prefix (e.g., '?name', '?age').
                If no variables are provided, the query will select all variables (SELECT *).

        Returns:
            SPARQLQuery: Amended query instance to allow method chaining.

        Raises:
            ValueError: If DISTINCT is already set (DISTINCT and REDUCED are mutually exclusive).

        Examples:
            >>> query.select_reduced("?name", "?age")
            SELECT REDUCED ?name ?age

            >>> query.select_reduced()
            SELECT REDUCED *
        """
        if self._distinct:
            raise ValueError("Cannot use both DISTINCT and REDUCED in the same query")
        self._reduced = True
        return self.select(*variables)

    def from_graph(self, graph_uri: str) -> 'SPARQLQuery':
        """Add FROM clause to the SPARQL query.

        The FROM clause specifies the default graph for the query. Multiple FROM
        clauses can be added to define a dataset consisting of the merge of the
        specified graphs.

        See Also:
            SPARQL 1.1 Query Language specification:
            https://www.w3.org/TR/sparql11-query/#specifyingDataset

        Args:
            graph_uri (str): The URI of the graph to add to the FROM clause.

        Returns:
            SPARQLQuery: Amended query instance to allow method chaining.

        Example:
            >>> query.from_graph("http://example.org/graph1")
            FROM <http://example.org/graph1>
        """
        sanitized_uri = sanitize_uri(graph_uri)
        self._from_graphs.append(sanitized_uri)
        return self

    def from_named_graph(self, graph_uri: str) -> 'SPARQLQuery':
        """
        Add a FROM NAMED clause to the SPARQL query.

        The FROM NAMED clause specifies a named graph that should be available
        for querying within the dataset. Named graphs can be referenced using
        the GRAPH keyword in query patterns.

        See Also:
            SPARQL 1.1 Query Language specification:
            https://www.w3.org/TR/sparql11-query/#specifyingDataset

        Args:
            graph_uri (str): The URI of the named graph to include in the dataset.

        Returns:
            SPARQLQuery: Amended query instance to allow method chaining.

        Example:
            >>> query.from_named_graph("http://example.org/graph1")
            FROM NAMED <http://example.org/graph1>
        """
        """Add FROM NAMED clause"""
        sanitized_uri = sanitize_uri(graph_uri)
        self._from_named_graphs.append(sanitized_uri)
        return self

    def where(self, subject: Union[str, None], predicate: Union[str, None],
              obj: Union[str, int, float, bool, None],
              datatype: Optional[str] = None, lang: Optional[str] = None) -> 'SPARQLQuery':
        """
        Add a WHERE clause pattern to the SPARQL query.

        Args:
            subject: The subject of the triple pattern. Can be a variable (string) or None for
                    anonymous variable.
            predicate: The predicate of the triple pattern. Can be a variable (string) or None
                    for anonymous variable.
            obj: The object of the triple pattern. Can be a variable (string), literal value
                    (int, float, bool), or None for anonymous variable.
            datatype: Optional datatype for the object literal (e.g., 'xsd:string', 'xsd:int').
            lang: Optional language tag for string literals (e.g., 'en', 'fr').

        Returns:
            SPARQLQuery: Amended query instance to allow method chaining.

        Example:
            >>> query.where('?person', 'foaf:name', '?name')
            WHERE { ?person foaf:name ?name }
            >>> query.where('?person', 'foaf:age', 25, datatype='xsd:int')
            WHERE { ?person foaf:age 25^^xsd:int }
            >>> query.where('?person', 'rdfs:label', 'John', lang='en')
            WHERE { ?person rdfs:label 'John'@en }
            >>> query.where(None, 'rdf:type', 'foaf:Person')
            WHERE { ?anon rdf:type foaf:Person }
        """
        pattern = TripleElement(subject, predicate, obj, datatype, lang)
        self._context_stack[-1].append(pattern)
        return self

    def optional(self, callback: Callable[['SPARQLQuery'], None]) -> 'SPARQLQuery':
        """
        Add an optional block to the SPARQL query.

        This method creates an OPTIONAL block in the SPARQL query by executing the provided
        callback function within a new context. Any patterns added during the callback
        execution will be wrapped in an OPTIONAL clause.

        Args:
            callback (Callable[['SPARQLQuery'], None]): A function that takes a SPARQLQuery
                instance and adds patterns to it. These patterns will be made optional.

        Returns:
            SPARQLQuery: Amended query instance to allow method chaining.

        Example:
            >>> query.optional(lambda q: q.where('?person', 'foaf:mbox', '?email'))
            WHERE {
                OPTIONAL {
                    ?person foaf:mbox ?email .
                }
            }

        Note:
            The callback function should use the passed SPARQLQuery instance to add
            the desired optional patterns. All patterns added within the callback
            will be grouped together in a single OPTIONAL block.
        """
        optional_patterns = []
        self._context_stack.append(optional_patterns)
        callback(self)
        self._context_stack.pop()
        self._context_stack[-1].append(OptionalBlock(optional_patterns))
        return self

    def union(self, *callbacks: Callable[['SPARQLQuery'], None]) -> 'SPARQLQuery':
        """
        Create a UNION block in the SPARQL query.

        A UNION block allows for alternative graph patterns, where the query will match
        if any of the patterns match. Each callback function defines one alternative
        pattern within the union.

        Args:
            *callbacks: Variable number of callback functions that each take a SPARQLQuery
                       instance and define graph patterns for one branch of the union.
                       Each callback is executed in its own context to build separate
                       pattern groups.

        Returns:
            SPARQLQuery: Amended query instance to allow method chaining.

        Example:
            >>> query.union(
            ...     lambda q: q.where('?person', 'foaf:name', '?identifier'),
            ...     lambda q: q.where('?person', 'foaf:mbox', '?identifier')
            ... )
            WHERE {
                {
                    ?person foaf:name ?identifier .
                }
                UNION
                {
                    ?person foaf:mbox ?identifier .
                }
            }
        """
        pattern_groups = []

        for callback in callbacks:
            group_patterns = []
            self._context_stack.append(group_patterns)
            callback(self)
            self._context_stack.pop()
            pattern_groups.append(group_patterns)

        self._context_stack[-1].append(UnionBlock(pattern_groups))
        return self

    def minus(self, callback: Callable[['SPARQLQuery'], None]) -> 'SPARQLQuery':
        """Add a MINUS block to the SPARQL query.

        The MINUS block removes solutions from the query results. It subtracts matches
        from the overall result set based on the patterns defined in the callback.

        Args:
            callback (Callable[['SPARQLQuery'], None]): A function that takes a SPARQLQuery
                instance and adds patterns to it. Solutions matching these patterns will
                be removed from the results.

        Returns:
            SPARQLQuery: Amended query instance to allow method chaining.

        Example:
            >>> query.minus(lambda q: q.where('?person', 'foaf:status', '"inactive"'))
            WHERE {
                MINUS {
                    ?person foaf:status "inactive" .
                }
            }
        """
        minus_patterns = []
        self._context_stack.append(minus_patterns)
        callback(self)
        self._context_stack.pop()

        self._context_stack[-1].append(MinusBlock(minus_patterns))
        return self

    def graph(self, graph_uri: Union[str, None], callback: Callable[['SPARQLQuery'], None]) -> 'SPARQLQuery':
        """Add a GRAPH block to query a specific named graph.

        The GRAPH keyword allows querying patterns within a specific named graph.
        This is used in conjunction with FROM NAMED to query named graphs within
        the dataset.

        See Also:
            SPARQL 1.1 Query Language specification:
            https://www.w3.org/TR/sparql11-query/#specifyingDataset

        Args:
            graph_uri (Union[str, None]): The URI of the named graph to query, or a
                variable (e.g., '?g') to match against any named graph. Can be None
                for an anonymous graph variable.
            callback (Callable[['SPARQLQuery'], None]): A function that takes a SPARQLQuery
                instance and adds patterns to query within the specified graph.

        Returns:
            SPARQLQuery: Amended query instance to allow method chaining.

        Example:
            >>> query.from_named_graph('http://example.org/contacts')
            >>> query.graph('http://example.org/contacts', lambda q: q
            ...     .where('?person', 'foaf:name', '?name')
            ...     .where('?person', 'foaf:mbox', '?email')
            ... )
            FROM NAMED <http://example.org/contacts>
            WHERE {
                GRAPH <http://example.org/contacts> {
                    ?person foaf:name ?name .
                    ?person foaf:mbox ?email .
                }
            }
        """
        graph_patterns = []
        self._context_stack.append(graph_patterns)
        callback(self)
        self._context_stack.pop()

        self._context_stack[-1].append(GraphBlock(graph_uri, graph_patterns))
        return self

    def filter(self, condition: str) -> 'SPARQLQuery':
        """Add a FILTER condition to constrain query results.

        FILTER expressions are used to restrict the solutions based on boolean
        conditions. The condition can use SPARQL built-in functions and operators.

        Args:
            condition (str): A SPARQL filter expression (e.g., '?age > 18',
                'BOUND(?email)', 'REGEX(?name, "^A")').

        Returns:
            SPARQLQuery: Amended query instance to allow method chaining.

        Example:
            >>> query.filter('?age > 18')
            WHERE {
                FILTER (?age > 18)
            }
        """
        self._context_stack[-1].append(FilterElement(condition))
        return self

    def filter_equals(self, variable: str, value: Any, datatype: Optional[str] = None) -> 'SPARQLQuery':
        """Add a FILTER condition for equality comparison.

        This is a convenience method for filtering based on variable equality.
        The value is automatically formatted as a literal.

        Args:
            variable (str): The variable name to filter (must include '?' or '$' prefix).
            value (Any): The value to compare against (string, int, float, or bool).
            datatype (Optional[str]): Optional datatype URI for the literal value.

        Returns:
            SPARQLQuery: Amended query instance to allow method chaining.

        Example:
            >>> query.filter_equals('?age', 25)
            WHERE {
                FILTER (?age = 25)
            }
        """
        var = sanitize_variable(variable)
        val = format_literal(value, datatype)
        return self.filter(f"{var} = {val}")

    def filter_regex(self, variable: str, pattern: str, flags: Optional[str] = None) -> 'SPARQLQuery':
        """Add a FILTER condition for regular expression matching.

        This method creates a REGEX filter to match variable values against a pattern.
        The pattern is automatically escaped for safe use in SPARQL.

        Args:
            variable (str): The variable name to filter (must include '?' or '$' prefix).
            pattern (str): The regular expression pattern to match.
            flags (Optional[str]): Optional regex flags ('i' for case-insensitive, etc.).

        Returns:
            SPARQLQuery: Amended query instance to allow method chaining.

        Example:
            >>> query.filter_regex('?name', '^A', 'i')
            WHERE {
                FILTER (REGEX(?name, "^A", "i"))
            }
        """
        var = sanitize_variable(variable)
        escaped_pattern = escape_string(pattern)

        if flags:
            condition = f'REGEX({var}, "{escaped_pattern}", "{flags}")'
        else:
            condition = f'REGEX({var}, "{escaped_pattern}")'

        return self.filter(condition)

    def filter_exists(self, callback: Callable[['SPARQLQuery'], None]) -> 'SPARQLQuery':
        """Add a FILTER EXISTS condition to require pattern matching.

        FILTER EXISTS tests whether a pattern matches in the data. The query only
        returns results where the EXISTS pattern finds at least one match.

        Args:
            callback (Callable[['SPARQLQuery'], None]): A function that takes a SPARQLQuery
                instance and adds patterns that must exist for the filter to pass.

        Returns:
            SPARQLQuery: Amended query instance to allow method chaining.

        Example:
            >>> query.filter_exists(lambda q: q
            ...     .where('?person', 'foaf:interest', '?interest')
            ... )
            WHERE {
                FILTER (EXISTS {
                    ?person foaf:interest ?interest .
                })
            }
        """
        exists_patterns = []
        self._context_stack.append(exists_patterns)
        callback(self)
        self._context_stack.pop()

        # Build the EXISTS pattern
        exists_lines = ["{"]
        for pattern in exists_patterns:
            exists_lines.append(pattern.to_sparql(4))
        exists_lines.append("  }")

        exists_str = "\n".join(exists_lines)
        return self.filter(f"EXISTS {exists_str}")

    def filter_not_exists(self, callback: Callable[['SPARQLQuery'], None]) -> 'SPARQLQuery':
        """Add a FILTER NOT EXISTS condition to require pattern absence.

        FILTER NOT EXISTS tests whether a pattern does NOT match in the data. The query
        only returns results where the NOT EXISTS pattern finds no matches.

        Args:
            callback (Callable[['SPARQLQuery'], None]): A function that takes a SPARQLQuery
                instance and adds patterns that must NOT exist for the filter to pass.

        Returns:
            SPARQLQuery: Amended query instance to allow method chaining.

        Example:
            >>> query.filter_not_exists(lambda q: q
            ...     .where('?person', 'foaf:status', '"banned"')
            ... )
            WHERE {
                FILTER (NOT EXISTS {
                    ?person foaf:status "banned" .
                })
            }
        """
        not_exists_patterns = []
        self._context_stack.append(not_exists_patterns)
        callback(self)
        self._context_stack.pop()

        # Build the NOT EXISTS pattern
        not_exists_lines = ["{"]
        for pattern in not_exists_patterns:
            not_exists_lines.append(pattern.to_sparql(4))
        not_exists_lines.append("  }")

        not_exists_str = "\n".join(not_exists_lines)
        return self.filter(f"NOT EXISTS {not_exists_str}")

    def property_path(self, subject: Union[str, None], path: str, obj: Union[str, None]) -> 'SPARQLQuery':
        """Add a property path pattern to the query (e.g., foaf:knows+, etc.).

        Property paths provide a way to match more complex patterns using path expressions.
        This method is a convenience wrapper around where() for property paths.

        Property path operators:
            * : Zero or more occurrences
            + : One or more occurrences
            ? : Zero or one occurrence
            / : Sequence (path concatenation)
            | : Alternative paths
            ^ : Inverse property

        Args:
            subject (Union[str, None]): The subject of the triple pattern (variable, URI, or None).
            path (str): The property path expression (e.g., 'foaf:knows+', 'foaf:knows/foaf:name').
            obj (Union[str, None]): The object of the triple pattern (variable, URI, or None).

        Returns:
            SPARQLQuery: Amended query instance to allow method chaining.

        Example:
            >>> query.property_path('?person', 'foaf:knows+', '?friend')
            WHERE {
                ?person foaf:knows+ ?friend .
            }
        """
        return self.where(subject, path, obj)

    def order_by(self, variable: str, descending: bool = False) -> 'SPARQLQuery':
        """Add an ORDER BY clause to sort query results.

        Results can be ordered by one or more variables in ascending or descending order.
        Call this method multiple times to order by multiple variables.

        Args:
            variable (str): The variable name to order by (must include '?' or '$' prefix).
            descending (bool): If True, sort in descending order; if False (default),
                sort in ascending order.

        Returns:
            SPARQLQuery: Amended query instance to allow method chaining.

        Example:
            >>> query.order_by('?name').order_by('?age', descending=True)
            ORDER BY ?name DESC(?age)
        """
        var = sanitize_variable(variable)
        self._order_by.append((var, descending))
        return self

    def group_by(self, *variables: str) -> 'SPARQLQuery':
        """Add a GROUP BY clause for result aggregation.

        GROUP BY groups results by the specified variables, typically used with
        aggregate functions like COUNT, SUM, AVG, etc.

        Args:
            *variables (str): Variable names to group by (must include '?' or '$' prefix).
                Multiple variables can be provided.

        Returns:
            SPARQLQuery: Amended query instance to allow method chaining.

        Example:
            >>> query.group_by('?category', '?type')
            GROUP BY ?category ?type
        """
        for var in variables:
            sanitized_var = sanitize_variable(var)
            self._group_by.append(sanitized_var)
        return self

    def having(self, condition: str) -> 'SPARQLQuery':
        """Add a HAVING clause to filter grouped results.

        HAVING is used with GROUP BY to filter groups based on aggregate conditions.
        Multiple HAVING conditions are combined with AND.

        Args:
            condition (str): A SPARQL expression to filter groups
                (e.g., 'COUNT(?item) > 5', 'AVG(?price) < 100').

        Returns:
            SPARQLQuery: Amended query instance to allow method chaining.

        Example:
            >>> query.group_by('category').having('COUNT(?item) > 10')
            GROUP BY ?category
            HAVING (COUNT(?item) > 10)
        """
        self._having_conditions.append(condition)
        return self

    def limit(self, limit: int) -> 'SPARQLQuery':
        """Add a LIMIT clause to restrict the number of results.

        LIMIT specifies the maximum number of solutions to return from the query.

        Args:
            limit (int): Maximum number of results to return. Must be a non-negative integer.

        Returns:
            SPARQLQuery: Amended query instance to allow method chaining.

        Raises:
            ValueError: If limit is not a non-negative integer.

        Example:
            >>> query.limit(10)
            LIMIT 10
        """
        if not isinstance(limit, int) or limit < 0:
            raise ValueError("LIMIT must be a non-negative integer")
        self._limit_value = limit
        return self

    def offset(self, offset: int) -> 'SPARQLQuery':
        """Add an OFFSET clause to skip a number of results.

        OFFSET specifies how many solutions to skip before returning results.
        Often used with LIMIT for pagination.

        Args:
            offset (int): Number of results to skip. Must be a non-negative integer.

        Returns:
            SPARQLQuery: Amended query instance to allow method chaining.

        Raises:
            ValueError: If offset is not a non-negative integer.

        Example:
            >>> query.limit(10).offset(20)
            LIMIT 10
            OFFSET 20
        """
        if not isinstance(offset, int) or offset < 0:
            raise ValueError("OFFSET must be a non-negative integer")
        self._offset_value = offset
        return self

    def build(self) -> str:
        """Build the final SPARQL query string.

        Constructs a complete SPARQL SELECT query by combining all the configured
        components including prefixes, query modifiers (DISTINCT/REDUCED), variables,
        FROM clauses, WHERE patterns, filters, GROUP BY, HAVING, ORDER BY, LIMIT, and OFFSET.

        Returns:
            str: A properly formatted SPARQL query string with newline-separated clauses.

        Raises:
            ValueError: If both DISTINCT and REDUCED are set, as they are mutually exclusive
                   in SPARQL specification.

        Example:
            >>> builder = QueryBuilder()
            >>> builder.select("name").where("?person foaf:name ?name")
            >>> query = builder.build()
            >>> print(query)
            SELECT ?name
            WHERE {
              ?person foaf:name ?name .
            }
        """
        if self._distinct and self._reduced:
            raise ValueError("Cannot use both DISTINCT and REDUCED in the same query")

        query_parts = []

        # Add prefixes
        for prefix, uri in self._prefixes.items():
            query_parts.append(f"PREFIX {prefix}: <{uri}>")

        if self._prefixes:
            query_parts.append("")

        # Add query type and projection
        select_clause = "SELECT"
        if self._distinct:
            select_clause += " DISTINCT"
        elif self._reduced:
            select_clause += " REDUCED"

        if self._variables:
            select_clause += " " + " ".join(self._variables)
        else:
            select_clause += " *"

        query_parts.append(select_clause)

        # Add FROM clauses
        for graph in self._from_graphs:
            query_parts.append(f"FROM <{graph}>")

        for graph in self._from_named_graphs:
            query_parts.append(f"FROM NAMED <{graph}>")

        # Add WHERE clause
        query_parts.append("WHERE {")

        for pattern in self._patterns:
            query_parts.append(pattern.to_sparql(2))

        query_parts.append("}")

        # Add GROUP BY
        if self._group_by:
            query_parts.append(f"GROUP BY {' '.join(self._group_by)}")

        # Add HAVING
        if self._having_conditions:
            having_clause = "HAVING (" + " && ".join(self._having_conditions) + ")"
            query_parts.append(having_clause)

        # Add ORDER BY
        if self._order_by:
            order_clauses = []
            for var, desc in self._order_by:
                if desc:
                    order_clauses.append(f"DESC({var})")
                else:
                    order_clauses.append(var)
            query_parts.append(f"ORDER BY {' '.join(order_clauses)}")

        # Add LIMIT and OFFSET
        if self._limit_value is not None:
            query_parts.append(f"LIMIT {self._limit_value}")

        if self._offset_value is not None:
            query_parts.append(f"OFFSET {self._offset_value}")

        return "\n".join(query_parts)

    def __str__(self) -> str:
        """Return the SPARQL query string representation.

        This method allows the SPARQLQuery instance to be used directly in string
        contexts (e.g., print(), str()). It's a convenience wrapper around build().

        Returns:
            str: The complete SPARQL query string.

        Example:
            >>> query = SPARQLQuery().select('name').where('?person', 'foaf:name', '?name')
            >>> print(query)
            SELECT ?name
            WHERE {
              ?person foaf:name ?name .
            }
        """
        return self.build()


# -----------------------------------------------------------------------------
# Convenience functions

def select(*variables: str) -> SPARQLQuery:
    """Convenience function to create a new SELECT query with the specified variables.

    This function initializes a new SPARQLQuery instance and applies the SELECT
    clause with the provided variables.

    Args:
        *variables (str): Variable names to select in the SPARQL query. Variables
            must include the '?' or '$' prefix (e.g., '?name', '?age').
            If no variables are provided, the query will select all variables (SELECT *).

    Returns:
        SPARQLQuery: A new SPARQLQuery instance configured with the SELECT clause
            containing the specified variables.

    Examples:
        >>> select("?name", "?age", "?email")
        SELECT ?name ?age ?email

        >>> select()
        SELECT *
    """
    return SPARQLQuery().select(*variables)


def select_distinct(*variables: str) -> SPARQLQuery:
    """Convenience function to create a new SELECT DISTINCT query with the specified variables.

    This function initializes a new SPARQLQuery instance and applies the SELECT DISTINCT
    clause with the provided variables. SELECT DISTINCT ensures that duplicate result
    rows are eliminated from the query results.

    Args:
        *variables (str): Variable names to select in the SPARQL query. Variables
            must include the '?' or '$' prefix (e.g., '?name', '?age').
            If no variables are provided, the query will select all variables (SELECT *).

    Returns:
        SPARQLQuery: A new SPARQLQuery instance configured with the SELECT DISTINCT
            clause and the specified variables.

    Examples:
        >>> select_distinct('?subject', '?object')
        SELECT DISTINCT ?subject ?object

        >>> select_distinct()
        SELECT DISTINCT *
    """
    return SPARQLQuery().select_distinct(*variables)


def select_reduced(*variables: str) -> SPARQLQuery:
    """Convenience function to create a new SELECT REDUCED query with the specified variables.

    This function initializes a new SPARQLQuery instance and applies the SELECT REDUCED
    clause with the provided variables. SELECT REDUCED clause returns a solution sequence with
    duplicate solutions eliminated in an implementation-dependent way. Unlike SELECT DISTINCT,
    the order and method of duplicate elimination is not specified.

    Args:
        *variables (str): Variable names to select in the SPARQL query. Variables
            must include the '?' or '$' prefix (e.g., '?name', '?age').
            If no variables are provided, the query will select all variables (SELECT *).

    Returns:
        SPARQLQuery: A new SPARQLQuery instance configured with SELECT REDUCED
            clause for the specified variables.

    Examples:
        >>> select_reduced("?subject", "?predicate", "?object")
        SELECT REDUCED ?subject ?predicate ?object

        >>> select_reduced()
        SELECT REDUCED *
    """
    return SPARQLQuery().select_reduced(*variables)
