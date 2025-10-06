"""
SPARQL value formatting and validation functions

These functions validate and format SPARQL values (subjects, predicates, objects)
to ensure they are safe for use in SPARQL queries and prevent injection attacks.
"""

import re
from typing import Any, Optional, Union
from urllib.parse import quote, unquote, urlparse


def escape_string(value: str) -> str:
    """Escape special characters in string literals"""
    if not isinstance(value, str):
        value = str(value)

    # Escape backslashes first
    value = value.replace('\\', '\\\\')
    # Escape quotes
    value = value.replace('"', '\\"')
    value = value.replace("'", "\\'")
    # Escape newlines and other control characters
    value = value.replace('\n', '\\n')
    value = value.replace('\r', '\\r')
    value = value.replace('\t', '\\t')

    return value


def sanitize_uri(uri: str) -> str:
    """Percent-encode a URI for safe use in SPARQL

    Uses urllib.parse.quote for RFC 3986 compliant URI encoding.
    This handles real-world URIs that may contain spaces or other special characters.

    Assumes the URI has already been validated (e.g., with is_valid_uri()).
    This function only performs the encoding transformation.

    Leading/trailing whitespace is automatically stripped as it's never valid in URIs.
    Note: Angle brackets < > should NOT be included in the uri parameter - they are
    handled by the calling code.
    """
    if not isinstance(uri, str):
        raise ValueError("URI must be a string")

    # Strip leading/trailing whitespace - always a mistake for URIs
    uri = uri.strip()

    # Basic validation
    if not uri:
        raise ValueError("URI cannot be empty")

    # Use urllib.parse.quote for proper URI encoding
    # First unquote to avoid double-encoding, then quote again
    # This ensures URIs like "my%20file" don't become "my%2520file"
    decoded_uri = unquote(uri)

    # safe parameter: characters that should NOT be encoded
    # We keep ':/?#[]@!$&\'()*+,;=' as they are valid in URIs (RFC 3986)
    # This handles spaces, quotes, and other special characters properly
    encoded_uri = quote(decoded_uri, safe=':/?#[]@!$&\'()*+,;=')

    return encoded_uri


def is_valid_uri(uri: str) -> bool:
    """Check if a string is a valid URI using urllib.parse

    Validates both URI structure (must have a scheme) and checks for dangerous
    characters that could break SPARQL syntax.

    A valid URI should have a scheme (e.g., http, https, mailto, urn, etc.)
    and must not contain characters that could cause injection attacks.

    Note: Angle brackets < > should NOT be in the uri parameter - they are
    SPARQL delimiters handled by the calling code.
    """
    if not isinstance(uri, str):
        return False

    # Strip whitespace for checking (but not angle brackets - those should be removed by caller)
    uri = uri.strip()

    if not uri:
        return False

    # Check for dangerous characters that could break SPARQL syntax
    # These cannot be safely encoded and should be rejected
    # Note: spaces are allowed (will be percent-encoded by sanitize_uri)
    # Note: # is allowed as it's a valid URI fragment identifier
    dangerous_chars = ['\n', '\r', '\t', '<', '>', '{', '}', '|', '\\', '^', '`', '[', ']']
    for char in dangerous_chars:
        if char in uri:
            return False  # Invalid - contains dangerous character

    # Check URI structure
    try:
        parsed = urlparse(uri)
        # A valid URI must have a scheme (http, https, mailto, urn, etc.)
        # This helps distinguish URIs from plain strings
        return bool(parsed.scheme)
    except Exception:
        return False


def sanitize_variable(var: str) -> str:
    """Validate variable names

    Leading/trailing whitespace is automatically stripped as it's never valid in variable names.
    """
    if not isinstance(var, str):
        raise ValueError("Variable must be a string")

    # Strip leading/trailing whitespace and variable prefixes
    var = var.strip().lstrip('?$')

    # Validate variable name (alphanumeric and underscore)
    if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', var):
        raise ValueError(f"Invalid variable name: {var}")

    return var


def sanitize_property_path(path: str) -> str:
    """Validate and sanitize property path expressions

    Property paths can contain:
    - URI references (prefixed or full URIs in angle brackets)
    - Path operators: * + ? | / ^
    - Parentheses for grouping
    - Negation with !

    This prevents injection by ensuring the path only contains valid SPARQL property path syntax.
    """
    if not isinstance(path, str):
        raise ValueError("Property path must be a string")

    if not path:
        raise ValueError("Property path cannot be empty")

    # Check for dangerous characters that could break out of the predicate position
    dangerous_chars = ['.', ';', '#', '\n', '\r', '\t', '{', '}', '[', ']']
    for char in dangerous_chars:
        if char in path:
            raise ValueError(f"Invalid character in property path: {repr(char)}")

    # Validate that the path is a reasonable property path expression
    # It should contain either:
    # 1. A URI pattern (prefix:name or <full-uri>)
    # 2. Property path operators: * + ? | / ^ ( ) !
    # 3. Combinations of the above

    # Remove all valid property path components to see if anything suspicious remains
    cleaned = path

    # Remove URIs in angle brackets
    cleaned = re.sub(r'<[^<>]+>', '', cleaned)

    # Remove prefixed names (namespace:localname)
    cleaned = re.sub(r'[a-zA-Z_][\w\-]*:[a-zA-Z_][\w\-]*', '', cleaned)

    # Remove valid property path operators and whitespace
    cleaned = re.sub(r'[*+?|/^()!\s]', '', cleaned)

    # If anything remains after removing valid components, it's suspicious
    if cleaned:
        raise ValueError(f"Property path contains invalid characters: {repr(cleaned)}")

    return path


def format_literal(value: Any, datatype: Optional[str] = None, lang: Optional[str] = None) -> str:
    """Format a literal value with optional datatype or language tag"""
    if isinstance(value, bool):
        return "true" if value else "false"
    elif isinstance(value, int) or isinstance(value, float):
        return str(value)
    else:
        escaped = escape_string(str(value))
        literal = f'"{escaped}"'

        if lang:
            literal += f"@{lang}"
        elif datatype:
            literal += f"^^<{sanitize_uri(datatype)}>"

        return literal


def format_subject(term: str) -> str:
    """Format a subject term (URI, variable, or prefixed name)

    This function validates and formats subject terms for safe use in SPARQL queries.
    Does not support None for anonymous variables - that's handled by the query builder.

    Leading/trailing whitespace is automatically stripped from string inputs.

    Args:
        term: Subject string (variable, URI, or prefixed name)

    Returns:
        Formatted subject string safe for SPARQL

    Raises:
        ValueError: If term is not a valid subject format
    """
    # Must be a string
    if not isinstance(term, str):
        raise ValueError(f"Subject must be a string, got {type(term)}")

    # Strip leading/trailing whitespace
    term = term.strip()

    # Empty string check
    if not term:
        raise ValueError("Subject cannot be an empty string")

    # Variable
    if term.startswith('?') or term.startswith('$'):
        return f"?{sanitize_variable(term)}"

    # Check for simple prefixed name pattern first (most common case)
    if re.match(r'^[a-zA-Z_][\w\-]*:[a-zA-Z_][\w\-]+$', term):
        return term

    # URI in angle brackets - must have matching < and >
    if term.startswith('<'):
        if not term.endswith('>'):
            raise ValueError(f"Invalid subject: URI starting with '<' must end with '>': {repr(term)}")
        inner_uri = term[1:-1].strip()
        if not inner_uri:
            raise ValueError("Subject URI cannot be empty")
        if not is_valid_uri(inner_uri):
            raise ValueError(f"Invalid URI in subject: {repr(inner_uri)}")
        return f"<{sanitize_uri(inner_uri)}>"

    # Full URI with scheme (e.g., http://...)
    if is_valid_uri(term):
        return f"<{sanitize_uri(term)}>"

    # Complex prefixed name with dots
    if ':' in term:
        parts = term.split(':', 1)
        if len(parts) == 2:
            prefix, local = parts
            if not re.match(r'^[a-zA-Z_][\w\-]*$', prefix):
                raise ValueError(f"Invalid namespace prefix in subject: {repr(prefix)}")
            if not re.match(r'^[a-zA-Z_][\w\-\.]*$', local):
                raise ValueError(f"Invalid local name in subject: {repr(local)}")
            return term
        else:
            raise ValueError(f"Invalid prefixed name format: {repr(term)}")

    # Check for dangerous characters to provide better error messages
    dangerous_chars = [';', '#', '\n', '\r', '\t', '{', '}', '[', ']', ' ']
    for char in dangerous_chars:
        if char in term:
            raise ValueError(
                f"Invalid subject: contains forbidden character {repr(char)}. "
                f"Subjects must be valid URIs, prefixed names, or variables."
            )

    raise ValueError(
        f"Invalid subject format: {repr(term)}. "
        f"Must be a variable (?name), URI (<uri> or http://...), or "
        f"prefixed name (prefix:name)"
    )


def format_predicate(term: str) -> str:
    """Format a predicate term (URI, variable, property path, or 'a')

    This function validates and formats predicate terms for safe use in SPARQL queries.
    Does not support None for anonymous variables - that's handled by the query builder.

    Leading/trailing whitespace is automatically stripped from string inputs.

    Args:
        term: Predicate string (variable, URI, prefixed name, or property path)

    Returns:
        Formatted predicate string safe for SPARQL

    Raises:
        ValueError: If term is not a valid predicate format
    """
    # Must be a string
    if not isinstance(term, str):
        raise ValueError(f"Predicate must be a string, got {type(term)}")

    # Strip leading/trailing whitespace
    term = term.strip()

    # Empty string check
    if not term:
        raise ValueError("Predicate cannot be an empty string")

    # Variable
    if term.startswith('?') or term.startswith('$'):
        return f"?{sanitize_variable(term)}"

    # Special case: 'a' is shorthand for rdf:type
    if term == 'a':
        return 'a'

    # Check for simple prefixed name pattern first (most common case)
    if re.match(r'^[a-zA-Z_][\w\-]*:[a-zA-Z_][\w\-]+$', term):
        return term

    # URI in angle brackets - must have matching < and >
    if term.startswith('<'):
        if not term.endswith('>'):
            raise ValueError(f"Invalid predicate: URI starting with '<' must end with '>': {repr(term)}")
        inner_uri = term[1:-1].strip()
        if not inner_uri:
            raise ValueError("Predicate URI cannot be empty")
        if not is_valid_uri(inner_uri):
            raise ValueError(f"Invalid URI in predicate: {repr(inner_uri)}")
        return f"<{sanitize_uri(inner_uri)}>"

    # Full URI with :// (e.g., http://example.org/resource)
    if '://' in term:
        if not is_valid_uri(term):
            raise ValueError(
                f"Invalid predicate: {repr(term)}. "
                f"Predicates must be valid URIs, prefixed names, or property paths."
            )
        return f"<{sanitize_uri(term)}>"

    # Property path (contains operators like +, *, ?, etc.)
    if any(op in term for op in ['*', '+', '?', '|', '/', '^', '(', ')']):
        return sanitize_property_path(term)

    # Full URI with scheme (e.g., urn:, mailto:)
    if is_valid_uri(term):
        return f"<{sanitize_uri(term)}>"

    # Check for any dangerous characters
    dangerous_chars = ['.', ';', '#', '\n', '\r', '\t', '{', '}', '[', ']', ' ']
    for char in dangerous_chars:
        if char in term:
            raise ValueError(
                f"Invalid predicate: contains forbidden character {repr(char)}. "
                f"Predicates must be valid URIs, prefixed names, or property paths."
            )

    # Complex prefixed name with dots
    if ':' in term:
        parts = term.split(':', 1)
        if len(parts) == 2:
            prefix, local = parts
            if not re.match(r'^[a-zA-Z_][\w\-]*$', prefix):
                raise ValueError(f"Invalid namespace prefix in predicate: {repr(prefix)}")
            if not re.match(r'^[a-zA-Z_][\w\-\.]*$', local):
                raise ValueError(f"Invalid local name in predicate: {repr(local)}")
            return term
        else:
            raise ValueError(f"Invalid prefixed name format: {repr(term)}")

    raise ValueError(
        f"Invalid predicate format: {repr(term)}. "
        f"Must be a variable (?name), URI (<uri> or http://...), "
        f"prefixed name (prefix:name), or property path (e.g., foaf:knows+)"
    )


def format_object(term: Union[str, int, float, bool],
                  datatype: Optional[str] = None,
                  lang: Optional[str] = None) -> str:
    """Format an object term (URI, variable, or literal)

    This function validates and formats object terms for safe use in SPARQL queries.
    Does not support None for anonymous variables - that's handled by the query builder.

    For URIs and variables: Leading/trailing whitespace is automatically stripped.
    For literal strings: Whitespace is preserved as it may be intentional user data.

    Args:
        term: Object value (variable, URI, or literal)
        datatype: Optional datatype URI for literal values
        lang: Optional language tag for literal values

    Returns:
        Formatted object string safe for SPARQL

    Raises:
        ValueError: If term is not a valid object format
    """
    # Literal (numbers and booleans) - handle before string processing
    if isinstance(term, (int, float, bool)):
        return format_literal(term, datatype, lang)

    # String can be either URI, variable, or literal - determine by pattern
    if isinstance(term, str):
        # For structural elements (URIs/variables), strip first to check pattern
        stripped_term = term.strip()

        # Empty string check (after stripping)
        if not stripped_term:
            raise ValueError("Object cannot be an empty string")

        # Variable - strip whitespace as it's structural
        if stripped_term.startswith('?') or stripped_term.startswith('$'):
            return f"?{sanitize_variable(stripped_term)}"

        # Check for simple prefixed name pattern first (most common case for URIs)
        if re.match(r'^[a-zA-Z_][\w\-]*:[a-zA-Z_][\w\-]+$', stripped_term):
            return stripped_term

        # URI in angle brackets - must have matching < and >
        if stripped_term.startswith('<'):
            if not stripped_term.endswith('>'):
                raise ValueError(f"Invalid object: URI starting with '<' must end with '>': {repr(stripped_term)}")
            inner_uri = stripped_term[1:-1].strip()
            if not inner_uri:
                raise ValueError("Object URI cannot be empty")
            if not is_valid_uri(inner_uri):
                raise ValueError(f"Invalid URI in object: {repr(inner_uri)}")
            return f"<{sanitize_uri(inner_uri)}>"

        # Full URI with scheme (e.g., http://...)
        if is_valid_uri(stripped_term):
            return f"<{sanitize_uri(stripped_term)}>"

        # Complex prefixed name with dots
        if ':' in stripped_term:
            parts = stripped_term.split(':', 1)
            if len(parts) == 2:
                prefix, local = parts
                if not re.match(r'^[a-zA-Z_][\w\-]*$', prefix):
                    # Not a valid prefix, treat as literal
                    return format_literal(term, datatype, lang)
                if not re.match(r'^[a-zA-Z_][\w\-\.]*$', local):
                    # Not a valid local name, treat as literal
                    return format_literal(term, datatype, lang)
                return stripped_term

        # Plain string - treat as literal (will be properly escaped)
        # Use original term to preserve intentional whitespace in user data
        return format_literal(term, datatype, lang)

    # Default: treat as literal
    return format_literal(str(term), datatype, lang)
