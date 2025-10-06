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
            SPARQLQuery: Returns self to allow method chaining

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
                can be provided without the '?' prefix (e.g., 'subject', 'predicate').
                If no variables are provided, the query will select all variables (SELECT *).

        Returns:
            SPARQLQuery: Returns self to allow method chaining.

        Examples:
            >>> query.select('name', 'age', 'email')
            SELECT ?name ?age ?email

            >>> query.select()
            SELECT *
        """
        for var in variables:
            sanitized_var = sanitize_variable(var)
            self._variables.append(f"?{sanitized_var}")
        return self

    def select_distinct(self, *variables: str) -> 'SPARQLQuery':
        """SELECT DISTINCT query that removes duplicate results from the result set.

        Args:
            *variables (str): Variable names to select in the SPARQL query. Variables
                can be provided without the '?' prefix (e.g., 'subject', 'predicate').
                If no variables are provided, the query will select all variables (SELECT *).

        Returns:
            SPARQLQuery: The query builder instance for method chaining.

        Raises:
            ValueError: If REDUCED is already set (DISTINCT and REDUCED are mutually exclusive).

        Examples:
            >>> query.select_distinct("name", "age")
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
                can be provided without the '?' prefix (e.g., 'subject', 'predicate').
                If no variables are provided, the query will select all variables (SELECT *).

        Returns:
            SPARQLQuery: The modified query object with REDUCED clause applied.

        Raises:
            ValueError: If DISTINCT is already set (DISTINCT and REDUCED are mutually exclusive).

        Examples:
            >>> query.select_reduced("name", "age")
            SELECT REDUCED ?name ?age

            >>> query.select_reduced()
            SELECT REDUCED *
        """
        if self._distinct:
            raise ValueError("Cannot use both DISTINCT and REDUCED in the same query")
        self._reduced = True
        return self.select(*variables)

    def from_graph(self, graph_uri: str) -> 'SPARQLQuery':
        """Add FROM clause"""
        sanitized_uri = sanitize_uri(graph_uri)
        self._from_graphs.append(sanitized_uri)
        return self

    def from_named_graph(self, graph_uri: str) -> 'SPARQLQuery':
        """Add FROM NAMED clause"""
        sanitized_uri = sanitize_uri(graph_uri)
        self._from_named_graphs.append(sanitized_uri)
        return self

    def where(self, subject: Union[str, None], predicate: Union[str, None],
              obj: Union[str, int, float, bool, None],
              datatype: Optional[str] = None, lang: Optional[str] = None) -> 'SPARQLQuery':
        """Add a triple pattern to current context

        Args:
            subject: URI string, variable (starting with ?), or None for anonymous variable
            predicate: URI string, 'a' for rdf:type, variable (starting with ?), or None for anonymous variable
            obj: URI string, literal value (str/int/float/bool), variable (starting with ?), or None for anonymous variable
            datatype: Optional datatype URI for literal objects
            lang: Optional language tag for literal objects

        Variables:
        - Explicit: Start with '?' (e.g., '?person', '?name') - use when you need to reference the variable
        - Anonymous: Use None when you don't need to reference the variable elsewhere

        URIs should contain '://' or be wrapped in <>
        Plain strings without '://' are treated as literals

        Examples:
            .where("?person", "foaf:name", "?name")  # Explicit variables
            .where("?person", "foaf:age", None)      # Anonymous variable for age (don't care about value)
            .where(None, "rdf:type", "foaf:Person")  # Anonymous subject
        """
        pattern = TripleElement(subject, predicate, obj, datatype, lang)
        self._context_stack[-1].append(pattern)
        return self

    def optional(self, callback: Callable[['SPARQLQuery'], None]) -> 'SPARQLQuery':
        """Add an OPTIONAL block using a callback"""
        optional_patterns = []
        self._context_stack.append(optional_patterns)
        callback(self)
        self._context_stack.pop()

        self._context_stack[-1].append(OptionalBlock(optional_patterns))
        return self

    def union(self, *callbacks: Callable[['SPARQLQuery'], None]) -> 'SPARQLQuery':
        """Add a UNION block with multiple alternatives"""
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
        """Add a MINUS block using a callback"""
        minus_patterns = []
        self._context_stack.append(minus_patterns)
        callback(self)
        self._context_stack.pop()

        self._context_stack[-1].append(MinusBlock(minus_patterns))
        return self

    def graph(self, graph_uri: Union[str, None], callback: Callable[['SPARQLQuery'], None]) -> 'SPARQLQuery':
        """Add a GRAPH block for querying named graphs"""
        graph_patterns = []
        self._context_stack.append(graph_patterns)
        callback(self)
        self._context_stack.pop()

        self._context_stack[-1].append(GraphBlock(graph_uri, graph_patterns))
        return self

    def filter(self, condition: str) -> 'SPARQLQuery':
        """Add a FILTER condition"""
        self._context_stack[-1].append(FilterElement(condition))
        return self

    def filter_equals(self, variable: str, value: Any, datatype: Optional[str] = None) -> 'SPARQLQuery':
        """Add a FILTER condition for equality"""
        var = f"?{sanitize_variable(variable)}"
        val = format_literal(value, datatype)
        return self.filter(f"{var} = {val}")

    def filter_regex(self, variable: str, pattern: str, flags: Optional[str] = None) -> 'SPARQLQuery':
        """Add a FILTER REGEX condition"""
        var = f"?{sanitize_variable(variable)}"
        escaped_pattern = escape_string(pattern)

        if flags:
            condition = f'REGEX({var}, "{escaped_pattern}", "{flags}")'
        else:
            condition = f'REGEX({var}, "{escaped_pattern}")'

        return self.filter(condition)

    def filter_exists(self, callback: Callable[['SPARQLQuery'], None]) -> 'SPARQLQuery':
        """Add a FILTER EXISTS condition"""
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
        """Add a FILTER NOT EXISTS condition"""
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
        """Add a property path pattern (e.g., foaf:knows+, foaf:knows*, etc.)

        Property path operators:
        - + : one or more
        - * : zero or more
        - ? : zero or one
        - / : sequence
        - | : alternative
        - ^ : inverse
        """
        return self.where(subject, path, obj)

    def order_by(self, variable: str, descending: bool = False) -> 'SPARQLQuery':
        """Add ORDER BY clause"""
        var = sanitize_variable(variable)
        self._order_by.append((var, descending))
        return self

    def group_by(self, *variables: str) -> 'SPARQLQuery':
        """Add GROUP BY clause"""
        for var in variables:
            sanitized_var = sanitize_variable(var)
            self._group_by.append(f"?{sanitized_var}")
        return self

    def having(self, condition: str) -> 'SPARQLQuery':
        """Add HAVING clause"""
        self._having_conditions.append(condition)
        return self

    def limit(self, limit: int) -> 'SPARQLQuery':
        """Add LIMIT clause"""
        if not isinstance(limit, int) or limit < 0:
            raise ValueError("LIMIT must be a non-negative integer")
        self._limit_value = limit
        return self

    def offset(self, offset: int) -> 'SPARQLQuery':
        """Add OFFSET clause"""
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
                    order_clauses.append(f"DESC(?{var})")
                else:
                    order_clauses.append(f"?{var}")
            query_parts.append(f"ORDER BY {' '.join(order_clauses)}")

        # Add LIMIT and OFFSET
        if self._limit_value is not None:
            query_parts.append(f"LIMIT {self._limit_value}")

        if self._offset_value is not None:
            query_parts.append(f"OFFSET {self._offset_value}")

        return "\n".join(query_parts)

    def __str__(self) -> str:
        return self.build()


# -----------------------------------------------------------------------------
# Convenience functions

def select(*variables: str) -> SPARQLQuery:
    """Create a new SELECT query with the specified variables.

    Args:
        *variables (str): Variable names to select in the SPARQL query. Variables
            can be provided without the '?' prefix (e.g., 'subject', 'predicate').
            If no variables are provided, the query will select all variables (SELECT *).

    Returns:
        SPARQLQuery: A new SPARQLQuery instance configured with the SELECT clause
            containing the specified variables.

    Examples:
        >>> select("name", "age", "email")
        SELECT ?name ?age ?email

        >>> select()
        SELECT *
    """
    return SPARQLQuery().select(*variables)


def select_distinct(*variables: str) -> SPARQLQuery:
    """Create a new SELECT DISTINCT query with the specified variables.

    This function initializes a new SPARQLQuery instance and applies the SELECT DISTINCT
    clause with the provided variables. SELECT DISTINCT ensures that duplicate result
    rows are eliminated from the query results.

    Args:
        *variables (str): Variable names to select in the SPARQL query. Variables
            can be provided without the '?' prefix (e.g., 'subject', 'predicate').
            If no variables are provided, the query will select all variables (SELECT *).

    Returns:
        SPARQLQuery: A new SPARQLQuery instance configured with the SELECT DISTINCT
            clause and the specified variables.

    Examples:
        >>> select_distinct('subject', 'object')
        SELECT DISTINCT ?subject ?object

        >>> select_distinct()
        SELECT DISTINCT *
    """
    return SPARQLQuery().select_distinct(*variables)


def select_reduced(*variables: str) -> SPARQLQuery:
    """
    Create a new SELECT REDUCED query with the specified variables.

    The SELECT REDUCED clause returns a solution sequence with duplicate solutions
    eliminated in an implementation-dependent way. Unlike SELECT DISTINCT, the
    order and method of duplicate elimination is not specified.

    Args:
        *variables (str): Variable names to select in the SPARQL query. Variables
            can be provided without the '?' prefix (e.g., 'subject', 'predicate').
            If no variables are provided, the query will select all variables (SELECT *).

    Returns:
        SPARQLQuery: A new SPARQLQuery instance configured with SELECT REDUCED
            clause for the specified variables.

    Examples:
        >>> select_reduced("subject", "predicate", "object")
        SELECT REDUCED ?subject ?predicate ?object

        >>> select_reduced()
        SELECT REDUCED *
    """
    return SPARQLQuery().select_reduced(*variables)
