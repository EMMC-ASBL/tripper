"""
SPARQL value formatting and validation using rdflib

This module provides improved formatting and validation for SPARQL values
(subjects, predicates, objects) using rdflib for proper RDF handling.
"""

import re
from typing import Any, Optional, Union
from rdflib import URIRef, Literal
from rdflib.namespace import XSD


# -----------------------------------------------------------------------------
# URI Validation and Formatting

def _validate_and_parse_uri(uri: str) -> URIRef:
    """Internal helper: validate URI and return URIRef object

    This is the single source of truth for URI validation.
    All URI validation logic is consolidated here.

    A valid URI must:
    1. Be a string
    2. Have a scheme (e.g., http, https, urn, etc.)
    3. Not contain dangerous characters that could break SPARQL syntax
    4. Parse correctly with rdflib
    5. Look like a real URI (has :// or is a known scheme like urn:, mailto:)

    Args:
        uri: URI string to validate

    Returns:
        rdflib URIRef object

    Raises:
        ValueError: If URI is invalid
    """
    if not isinstance(uri, str):
        raise ValueError(f"URI must be a string, got {type(uri)}")

    # Check for dangerous characters BEFORE stripping (newlines etc)
    dangerous_chars = ['\n', '\r', '\t', '<', '>', '{', '}', '|', '\\', '^', '`', ' ']
    if any(char in uri for char in dangerous_chars):
        raise ValueError(f"URI contains dangerous characters: {repr(uri)}")

    uri = uri.strip()
    if not uri:
        raise ValueError("URI cannot be empty")

    # Validate URI scheme
    # A URI should either:
    # 1. Contain :// (e.g., http://, https://, ftp://)
    # 2. Start with a known scheme without // (urn:, mailto:, tel:, doi:, etc.)
    if '://' in uri:
        # Has authority component - most common URIs
        pass
    elif uri.startswith(('urn:', 'mailto:', 'tel:', 'doi:', 'data:', 'file:', 'about:')):
        # Known schemes without //
        pass
    elif ':' in uri:
        # Has a colon but might just be a prefixed name like "foaf:name"
        # Additional check: if there are multiple colons and no //, it's probably not a URI
        colon_count = uri.count(':')
        if colon_count > 1 and '://' not in uri:
            # Check if it's a valid URN or similar
            if not uri.startswith(('urn:', 'mailto:', 'tel:', 'doi:', 'data:', 'file:', 'about:')):
                raise ValueError(f"Invalid URI scheme: {repr(uri)}")
        # Single colon without // is probably a prefixed name, not a URI
        # unless it's one of the known schemes above
        if colon_count == 1 and '://' not in uri:
            if not uri.startswith(('urn:', 'mailto:', 'tel:', 'doi:', 'data:', 'file:', 'about:')):
                raise ValueError(f"Invalid URI scheme: {repr(uri)}")
    else:
        raise ValueError(f"URI must have a scheme: {repr(uri)}")

    # Parse with rdflib for final validation
    try:
        return URIRef(uri)
    except Exception as e:
        raise ValueError(f"Cannot parse URI: {repr(uri)}: {e}")


def is_valid_uri(uri: str) -> bool:
    """Check if a string is a valid URI (no exceptions raised)

    This is a convenience wrapper around _validate_and_parse_uri() that
    returns a boolean instead of raising exceptions.

    Args:
        uri: String to validate as URI

    Returns:
        True if valid URI, False otherwise
    """
    try:
        _validate_and_parse_uri(uri)
        return True
    except (ValueError, Exception):
        return False


def validate_uri(uri: str) -> str:
    """Validate a URI and return it without angle brackets

    This function validates that a string is a valid URI but returns
    the raw URI string without formatting (no angle brackets).
    Use this for PREFIX declarations and FROM clauses.

    Args:
        uri: URI string to validate

    Returns:
        The validated URI string (without angle brackets)

    Raises:
        ValueError: If URI is invalid
    """
    uriref = _validate_and_parse_uri(uri)
    return str(uriref)


def format_uri(uri: str) -> str:
    """Format a URI using rdflib.URIRef with angle brackets

    This function validates a URI and returns it formatted for use
    in SPARQL triple patterns (wrapped in angle brackets).
    Use this for subjects, predicates, and objects in WHERE clauses.

    Args:
        uri: URI string to format

    Returns:
        N3-formatted URI (e.g., <http://example.org/resource>)

    Raises:
        ValueError: If URI is invalid
    """
    uriref = _validate_and_parse_uri(uri)
    return uriref.n3()


# -----------------------------------------------------------------------------
# Prefix Validation

def validate_prefixed_name(term: str) -> str:
    """Validate and return a prefixed name

    Valid patterns:
    - Simple: prefix:localname (e.g., foaf:Person)
    - With dots in local part: prefix:local.name (e.g., ex:person.name)
    - With hyphens: prefix:local-name

    Args:
        term: Prefixed name to validate

    Returns:
        The validated prefixed name

    Raises:
        ValueError: If not a valid prefixed name
    """
    if not isinstance(term, str):
        raise ValueError(f"Prefixed name must be a string, got {type(term)}")

    if ':' not in term:
        raise ValueError(f"Prefixed name must contain ':' separator: {repr(term)}")

    # Split only on first colon
    parts = term.split(':', 1)
    if len(parts) != 2:
        raise ValueError(f"Invalid prefixed name format: {repr(term)}")

    prefix, local = parts

    # Validate prefix: must start with letter or underscore
    if not re.match(r'^[a-zA-Z_][\w\-]*$', prefix):
        raise ValueError(f"Invalid prefix (must start with letter or underscore): {repr(term)}")

    # Validate local part: more permissive, allows dots
    if not re.match(r'^[a-zA-Z_][\w\-\.]*$', local):
        raise ValueError(f"Invalid local name (must start with letter or underscore): {repr(term)}")

    return term


def is_valid_prefixed_name(term: str) -> bool:
    """Check if a term is a valid prefixed name (prefix:localname)

    This is a convenience wrapper around validate_prefixed_name() that
    returns a boolean instead of raising exceptions.

    Args:
        term: String to check

    Returns:
        True if valid prefixed name, False otherwise
    """
    try:
        validate_prefixed_name(term)
        return True
    except (ValueError, Exception):
        return False


# -----------------------------------------------------------------------------
# Variable Validation

def validate_variable(var: str) -> str:
    """Validate and format a SPARQL variable

    Variables must:
    1. Start with '?' or '$'
    2. Have a name after the prefix
    3. Name must contain only alphanumeric characters and underscores

    Args:
        var: Variable string (must include ? or $ prefix)

    Returns:
        The validated variable

    Raises:
        ValueError: If not a valid variable
    """
    if not isinstance(var, str):
        raise ValueError("Variable must be a string")

    var = var.strip()

    if not var:
        raise ValueError("Variable cannot be empty")

    if var[0] not in ('?', '$'):
        raise ValueError(f"Variable must start with '?' or '$': {repr(var)}")

    if len(var) == 1:
        raise ValueError(f"Variable name cannot be empty: {repr(var)}")

    name = var[1:]
    if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', name):
        raise ValueError(f"Invalid variable name: {repr(var)}")

    return var


def is_valid_variable(var: str) -> bool:
    """Check if a string is a valid SPARQL variable

    This is a convenience wrapper around validate_variable() that
    returns a boolean instead of raising exceptions.

    Args:
        var: String to check

    Returns:
        True if valid variable, False otherwise
    """
    try:
        validate_variable(var)
        return True
    except (ValueError, Exception):
        return False


# -----------------------------------------------------------------------------
# Blank Node Support

def validate_blank_node(term: str) -> str:
    """Validate a blank node identifier

    Blank nodes start with '_:' followed by a valid name.
    Blank node names must start with letter or underscore and contain
    alphanumeric characters, underscores, hyphens, or dots.

    Args:
        term: Blank node string (e.g., _:b1)

    Returns:
        The validated blank node

    Raises:
        ValueError: If not a valid blank node
    """
    if not isinstance(term, str):
        raise ValueError(f"Blank node must be a string, got {type(term)}")

    term = term.strip()

    if not term.startswith('_:'):
        raise ValueError(f"Blank node must start with '_:': {repr(term)}")

    if len(term) == 2:
        raise ValueError(f"Blank node name cannot be empty: {repr(term)}")

    name = term[2:]
    # Blank node names must start with letter or underscore and contain alphanumeric, underscore, hyphen, or dot
    if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_\-\.]*$', name):
        raise ValueError(f"Invalid blank node name (must start with letter or underscore): {repr(term)}")

    return term


def is_blank_node(term: str) -> bool:
    """Check if a term is a blank node identifier

    This is a convenience wrapper around validate_blank_node() that
    returns a boolean instead of raising exceptions.

    Args:
        term: String to check

    Returns:
        True if valid blank node, False otherwise
    """
    try:
        validate_blank_node(term)
        return True
    except (ValueError, Exception):
        return False


# -----------------------------------------------------------------------------
# Property Path Support

def validate_property_path(path: str) -> str:
    """Validate a SPARQL property path expression

    Property paths can contain:
    - URI references (prefixed names or full URIs in angle brackets)
    - Path operators: * + ? | / ^ ( ) !
    - Whitespace for readability

    Property path operators: * + ? | / ^ ( ) !

    Args:
        path: Property path string

    Returns:
        The validated property path

    Raises:
        ValueError: If path contains invalid syntax
    """
    if not isinstance(path, str):
        raise ValueError(f"Property path must be a string, got {type(path)}")

    path = path.strip()
    if not path:
        raise ValueError("Property path cannot be empty")

    # Check for characters that could break SPARQL syntax
    dangerous_chars = ['.', ';', '#', '\n', '\r', '\t', '{', '}', '[', ']']
    for char in dangerous_chars:
        if char in path:
            raise ValueError(f"Invalid character in property path: {repr(char)}")

    # Validate structure by removing valid components
    # If anything suspicious remains, reject it
    cleaned = path

    # Remove URIs in angle brackets
    cleaned = re.sub(r'<[^<>]+>', '', cleaned)

    # Remove prefixed names
    cleaned = re.sub(r'[a-zA-Z_][\w\-]*:[a-zA-Z_][\w\-\.]*', '', cleaned)

    # Remove property path operators and whitespace
    cleaned = re.sub(r'[*+?|/^()!\s]', '', cleaned)

    # Remove 'a' (rdf:type shorthand)
    cleaned = re.sub(r'\ba\b', '', cleaned)

    # If anything remains, it's suspicious
    if cleaned:
        raise ValueError(f"Property path contains invalid syntax: remaining={repr(cleaned)}")

    return path


def is_property_path(term: str) -> bool:
    """Check if a term contains property path operators

    This is a convenience wrapper around validate_property_path() that
    returns a boolean instead of raising exceptions.

    Property path operators: * + ? | / ^ ( ) !

    Args:
        term: String to check

    Returns:
        True if contains property path operators, False otherwise
    """
    # Quick check: property paths must contain operators
    path_operators = ['*', '+', '?', '|', '/', '^', '(', ')', '!']
    if not any(op in term for op in path_operators):
        return False

    # Validate the full path
    try:
        validate_property_path(term)
        return True
    except (ValueError, Exception):
        return False


# -----------------------------------------------------------------------------
# Literal Formatting

def format_literal(value: Any,
                   datatype: Optional[str] = None,
                   lang: Optional[str] = None) -> str:
    """Format a literal value using rdflib.Literal

    Args:
        value: The literal value
        datatype: Optional datatype URI
        lang: Optional language tag

    Returns:
        N3-formatted literal
    """
    # Handle booleans specially (before type checking)
    if isinstance(value, bool):
        return "true" if value else "false"

    # Handle numeric types
    if isinstance(value, int):
        lit = Literal(value, datatype=XSD.integer)
        return lit.n3()

    if isinstance(value, float):
        lit = Literal(value, datatype=XSD.double)
        return lit.n3()

    # Handle strings with optional datatype or language
    if datatype:
        # Validate datatype URI if it looks like a full URI
        if '://' in datatype or datatype.startswith('<'):
            datatype_clean = datatype.strip('<>')
            if not is_valid_uri(datatype_clean):
                raise ValueError(f"Invalid datatype URI: {repr(datatype)}")
            lit = Literal(str(value), datatype=URIRef(datatype_clean))
        else:
            # Assume it's a prefixed name or XSD type
            lit = Literal(str(value), datatype=datatype)
        return lit.n3()

    if lang:
        lit = Literal(str(value), lang=lang)
        return lit.n3()

    # Plain literal
    lit = Literal(str(value))
    return lit.n3()


# -----------------------------------------------------------------------------
# Subject Formatting

def format_subject(term: str) -> str:
    """Format a subject term for SPARQL

    Subjects can be:
    - Variables: ?var or $var
    - URIs: <http://...> or http://...
    - Prefixed names: prefix:name
    - Blank nodes: _:b1

    Args:
        term: Subject term to format

    Returns:
        Formatted subject safe for SPARQL

    Raises:
        ValueError: If term is not a valid subject
    """
    if not isinstance(term, str):
        raise ValueError(f"Subject must be a string, got {type(term)}")

    term = term.strip()
    if not term:
        raise ValueError("Subject cannot be empty")

    # Variables
    if term.startswith('?') or term.startswith('$'):
        return validate_variable(term)

    # Blank nodes
    if term.startswith('_:'):
        return validate_blank_node(term)

    # URIs in angle brackets
    if term.startswith('<'):
        if not term.endswith('>'):
            raise ValueError(f"URI starting with '<' must end with '>': {repr(term)}")
        inner_uri = term[1:-1].strip()
        if not inner_uri:
            raise ValueError("URI cannot be empty")
        return format_uri(inner_uri)

    # Prefixed names
    if is_valid_prefixed_name(term):
        return validate_prefixed_name(term)

    # Full URIs without angle brackets - try to format, will raise if invalid
    try:
        return format_uri(term)
    except ValueError:
        pass

    # If we get here, it's not a valid subject
    raise ValueError(
        f"Invalid subject: {repr(term)}. "
        f"Must be a variable (?var), URI (<uri>), prefixed name (prefix:name), "
        f"or blank node (_:b1)"
    )


# -----------------------------------------------------------------------------
# Predicate Formatting

def format_predicate(term: str) -> str:
    """Format a predicate term for SPARQL

    Predicates can be:
    - Variables: ?var or $var
    - URIs: <http://...> or http://...
    - Prefixed names: prefix:name
    - 'a' shorthand for rdf:type
    - Property paths: prefix:path+ or complex paths

    Args:
        term: Predicate term to format

    Returns:
        Formatted predicate safe for SPARQL

    Raises:
        ValueError: If term is not a valid predicate
    """
    if not isinstance(term, str):
        raise ValueError(f"Predicate must be a string, got {type(term)}")

    term = term.strip()
    if not term:
        raise ValueError("Predicate cannot be empty")

    # Special case: 'a' is shorthand for rdf:type
    if term == 'a':
        return 'a'

    # Variables
    if term.startswith('?') or term.startswith('$'):
        return validate_variable(term)

    # URIs in angle brackets
    if term.startswith('<'):
        if not term.endswith('>'):
            raise ValueError(f"URI starting with '<' must end with '>': {repr(term)}")
        inner_uri = term[1:-1].strip()
        if not inner_uri:
            raise ValueError("URI cannot be empty")
        return format_uri(inner_uri)

    # Prefixed names (check before URIs since "foaf:name" could theoretically match URI patterns)
    if is_valid_prefixed_name(term):
        return validate_prefixed_name(term)

    # Full URIs - try to format, will raise if invalid
    try:
        return format_uri(term)
    except ValueError:
        pass

    # Property paths (detected by operators) - check last
    if is_property_path(term):
        return validate_property_path(term)

    # If we get here, it's not a valid predicate
    raise ValueError(
        f"Invalid predicate: {repr(term)}. "
        f"Must be a variable (?var), URI (<uri>), prefixed name (prefix:name), "
        f"'a' (rdf:type), or property path"
    )


# -----------------------------------------------------------------------------
# Object Formatting

def format_object(term: Union[str, int, float, bool],
                  datatype: Optional[str] = None,
                  lang: Optional[str] = None) -> str:
    """Format an object term for SPARQL

    Objects can be:
    - Variables: ?var or $var
    - URIs: <http://...> or http://...
    - Prefixed names: prefix:name
    - Blank nodes: _:b1
    - Literals: strings, numbers, booleans

    Args:
        term: Object term to format
        datatype: Optional datatype URI for literals
        lang: Optional language tag for string literals

    Returns:
        Formatted object safe for SPARQL

    Raises:
        ValueError: If term is not a valid object
    """
    # Handle non-string literals (numbers, booleans)
    if isinstance(term, (int, float, bool)) and not isinstance(term, bool):
        return format_literal(term, datatype, lang)

    # Special handling for booleans (before general type check)
    if isinstance(term, bool):
        return format_literal(term, datatype, lang)

    # Must be string from here on
    if not isinstance(term, str):
        raise ValueError(f"Object must be a string, number, or boolean, got {type(term)}")

    # Strip for structural elements, but we'll preserve original for literals
    stripped_term = term.strip()
    if not stripped_term:
        raise ValueError("Object cannot be empty")

    # Variables
    if stripped_term.startswith('?') or stripped_term.startswith('$'):
        return validate_variable(stripped_term)

    # Blank nodes
    if stripped_term.startswith('_:'):
        return validate_blank_node(stripped_term)

    # URIs in angle brackets
    if stripped_term.startswith('<'):
        if not stripped_term.endswith('>'):
            raise ValueError(f"URI starting with '<' must end with '>': {repr(stripped_term)}")
        inner_uri = stripped_term[1:-1].strip()
        if not inner_uri:
            raise ValueError("URI cannot be empty")
        return format_uri(inner_uri)

    # Prefixed names (check before URIs)
    if is_valid_prefixed_name(stripped_term):
        return validate_prefixed_name(stripped_term)

    # Full URIs - try to format, will fall through to literal if invalid
    try:
        return format_uri(stripped_term)
    except ValueError:
        pass

    # Everything else is treated as a literal
    # Use original term to preserve whitespace in user data
    return format_literal(term, datatype, lang)
