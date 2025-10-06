"""
SPARQL Query Builder - A fluent interface for building safe SPARQL queries

This package provides tools for constructing SPARQL queries with built-in
validation and sanitization to prevent injection attacks.

Public API:
-----------

Query Building:
    select()            - Create a new SELECT query
    select_distinct()   - Create a new SELECT DISTINCT query
    select_reduced()    - Create a new SELECT REDUCED query
    SPARQLQuery         - Main query builder class

Value Formatting (for external validation):
    format_subject()    - Format and validate a subject term
    format_predicate()  - Format and validate a predicate term
    format_object()     - Format and validate an object term

Example Usage:
-------------

Building queries:
    >>> from tripper.query_builder import select
    >>> query = (
    ...     select("person", "name")
    ...     .prefix("foaf", "http://xmlns.com/foaf/0.1/")
    ...     .where("?person", "foaf:name", "?name")
    ...     .where("?person", "a", "foaf:Person")
    ...     .limit(10)
    ... )
    >>> print(query.build())

Validating user input:
    >>> from tripper.query_builder import format_subject
    >>> user_input = "http://example.org/Alice"
    >>> safe_subject = format_subject(user_input)
    >>> # safe_subject is now '<http://example.org/Alice>'
"""

# Import public API from submodules
from .builder import (
    SPARQLQuery,
    select,
    select_distinct,
    select_reduced,
)

from .formatter import (
    format_subject,
    format_predicate,
    format_object,
)

# Define public API
__all__ = [
    # Query building
    'select',
    'select_distinct',
    'select_reduced',
    'SPARQLQuery',

    # Value formatting (for external validation)
    'format_subject',
    'format_predicate',
    'format_object',
]

__version__ = '1.0.0'
