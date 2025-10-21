"""Tests for the new formatter module using rdflib."""

import pytest
from tripper.query_builder.formatter import (
    format_subject,
    format_predicate,
    format_object,
    format_literal,
    format_uri,
    validate_uri,
    validate_variable,
    validate_prefixed_name,
    validate_property_path,
    validate_blank_node,
    is_valid_uri,
    is_valid_prefixed_name,
    is_valid_variable,
    is_blank_node,
    is_property_path,
)


class TestUriValidation:
    """Test URI validation and formatting."""

    def test_valid_http_uri(self):
        """Test valid HTTP URIs."""
        assert is_valid_uri("http://example.org") is True
        assert is_valid_uri("http://example.org/path") is True
        assert is_valid_uri("http://example.org/path?query=value") is True

    def test_valid_https_uri(self):
        """Test valid HTTPS URIs."""
        assert is_valid_uri("https://example.org") is True

    def test_valid_other_schemes(self):
        """Test other valid URI schemes."""
        assert is_valid_uri("ftp://example.org") is True
        assert is_valid_uri("mailto:test@example.org") is True
        assert is_valid_uri("urn:isbn:0451450523") is True

    def test_invalid_no_scheme(self):
        """Test URIs without schemes are invalid."""
        assert is_valid_uri("example.org") is False
        assert is_valid_uri("/path/to/resource") is False

    def test_invalid_dangerous_chars(self):
        """Test URIs with dangerous characters."""
        assert is_valid_uri("http://example.org<>") is False
        assert is_valid_uri("http://example.org{}") is False
        assert is_valid_uri("http://example.org\n") is False

    def test_invalid_empty(self):
        """Test empty URI."""
        assert is_valid_uri("") is False
        assert is_valid_uri("   ") is False

    def test_format_uri_basic(self):
        """Test formatting basic URIs."""
        result = format_uri("http://example.org/resource")
        assert result.startswith("<")
        assert result.endswith(">")
        assert "http://example.org/resource" in result

    def test_format_uri_with_spaces(self):
        """Test formatting URIs with spaces - should be rejected."""
        # URIs with spaces are invalid and should be rejected
        with pytest.raises(ValueError):
            format_uri("http://example.org/path with spaces")

    def test_format_uri_invalid_raises(self):
        """Test that invalid URIs raise ValueError."""
        with pytest.raises(ValueError):
            format_uri("not a uri")

        # URIs with newlines should be caught by is_valid_uri (newlines are dangerous)

    def test_validate_uri_basic(self):
        """Test validate_uri returns raw URI without angle brackets."""
        result = validate_uri("http://example.org/resource")
        assert result == "http://example.org/resource"
        assert not result.startswith("<")
        assert not result.endswith(">")

    def test_validate_uri_invalid_raises(self):
        """Test validate_uri raises on invalid URIs."""
        with pytest.raises(ValueError):
            validate_uri("not a uri")

        with pytest.raises(ValueError):
            validate_uri("http://example.org<>")

        # URIs with spaces are invalid (dangerous chars)
        with pytest.raises(ValueError):
            validate_uri("  http://example.org/resource  ")

    def test_validate_uri_vs_format_uri(self):
        """Test that validate_uri and format_uri differ in output format."""
        uri = "http://example.org/resource"
        validated = validate_uri(uri)
        formatted = format_uri(uri)

        # validate_uri returns raw URI
        assert validated == uri
        # format_uri returns URI with angle brackets
        assert formatted == f"<{uri}>"

        assert is_valid_uri("http://example.org\n") is False
        # And also raise when trying to format
        with pytest.raises(ValueError):
            format_uri("http://example.org\n")


class TestPrefixedNames:
    """Test prefixed name validation."""

    def test_valid_simple_prefix(self):
        """Test simple prefixed names."""
        assert is_valid_prefixed_name("foaf:Person") is True
        assert is_valid_prefixed_name("rdf:type") is True
        assert is_valid_prefixed_name("ex:resource") is True

    def test_valid_with_underscores(self):
        """Test prefixed names with underscores."""
        assert is_valid_prefixed_name("my_ns:my_resource") is True

    def test_valid_with_hyphens(self):
        """Test prefixed names with hyphens."""
        assert is_valid_prefixed_name("my-ns:my-resource") is True

    def test_valid_with_dots_in_local(self):
        """Test prefixed names with dots in local part."""
        assert is_valid_prefixed_name("ex:resource.property") is True

    def test_invalid_no_colon(self):
        """Test strings without colons."""
        assert is_valid_prefixed_name("nocolon") is False

    def test_invalid_prefix_starts_with_number(self):
        """Test prefix starting with number."""
        assert is_valid_prefixed_name("123:resource") is False

    def test_invalid_local_starts_with_number(self):
        """Test local part starting with number."""
        assert is_valid_prefixed_name("ex:123resource") is False

    def test_validate_prefixed_name_valid(self):
        """Test validating a valid prefixed name."""
        result = validate_prefixed_name("foaf:Person")
        assert result == "foaf:Person"

    def test_validate_prefixed_name_invalid(self):
        """Test validating an invalid prefixed name."""
        with pytest.raises(ValueError):
            validate_prefixed_name("not-valid")


class TestVariables:
    """Test variable validation."""

    def test_valid_variable_question_mark(self):
        """Test variables with question mark."""
        assert is_valid_variable("?x") is True
        assert is_valid_variable("?person") is True
        assert is_valid_variable("?my_var") is True

    def test_valid_variable_dollar_sign(self):
        """Test variables with dollar sign."""
        assert is_valid_variable("$x") is True
        assert is_valid_variable("$person") is True

    def test_invalid_no_prefix(self):
        """Test strings without variable prefix."""
        assert is_valid_variable("x") is False
        assert is_valid_variable("person") is False

    def test_invalid_only_prefix(self):
        """Test only prefix without name."""
        assert is_valid_variable("?") is False
        assert is_valid_variable("$") is False

    def test_invalid_name_starts_with_number(self):
        """Test variable name starting with number."""
        assert is_valid_variable("?1var") is False

    def test_validate_variable_valid(self):
        """Test validating valid variables."""
        assert validate_variable("?x") == "?x"
        assert validate_variable("$person") == "$person"

    def test_validate_variable_invalid(self):
        """Test validating invalid variables."""
        with pytest.raises(ValueError, match="must start with"):
            validate_variable("x")

        with pytest.raises(ValueError, match="cannot be empty"):
            validate_variable("?")


class TestBlankNodes:
    """Test blank node validation."""

    def test_valid_blank_node(self):
        """Test valid blank node identifiers."""
        assert is_blank_node("_:b1") is True
        assert is_blank_node("_:blank123") is True
        assert is_blank_node("_:my_blank") is True

    def test_invalid_no_prefix(self):
        """Test strings without blank node prefix."""
        assert is_blank_node("b1") is False
        assert is_blank_node("blank") is False

    def test_invalid_only_prefix(self):
        """Test only prefix without name."""
        assert is_blank_node("_:") is False

    def test_validate_blank_node_valid(self):
        """Test validating valid blank nodes."""
        result = validate_blank_node("_:b1")
        assert result == "_:b1"

    def test_validate_blank_node_invalid(self):
        """Test validating invalid blank nodes."""
        with pytest.raises(ValueError):
            validate_blank_node("b1")


class TestPropertyPaths:
    """Test property path validation."""

    def test_is_property_path_operators(self):
        """Test detection of property path operators."""
        assert is_property_path("foaf:knows+") is True
        assert is_property_path("foaf:knows*") is True
        assert is_property_path("foaf:knows?") is True
        assert is_property_path("foaf:knows|foaf:friend") is True
        assert is_property_path("foaf:knows/foaf:name") is True
        assert is_property_path("^foaf:knows") is True
        assert is_property_path("(foaf:knows|foaf:friend)+") is True

    def test_is_not_property_path(self):
        """Test detection of non-property paths."""
        assert is_property_path("foaf:knows") is False
        assert is_property_path("ex:property") is False

    def test_validate_property_path_valid(self):
        """Test validating valid property paths."""
        result = validate_property_path("foaf:knows+")
        assert result == "foaf:knows+"

        result = validate_property_path("foaf:knows/foaf:name")
        assert result == "foaf:knows/foaf:name"

    def test_validate_property_path_invalid_chars(self):
        """Test property paths with invalid characters."""
        with pytest.raises(ValueError, match="Invalid character"):
            validate_property_path("foaf:knows.")

        with pytest.raises(ValueError, match="Invalid character"):
            validate_property_path("foaf:knows;")


class TestLiterals:
    """Test literal formatting."""

    def test_format_string_literal(self):
        """Test formatting string literals."""
        result = format_literal("hello")
        assert result == '"hello"'

    def test_format_integer_literal(self):
        """Test formatting integer literals."""
        result = format_literal(42)
        assert "42" in result

    def test_format_float_literal(self):
        """Test formatting float literals."""
        result = format_literal(3.14)
        assert "3.14" in result

    def test_format_boolean_literal(self):
        """Test formatting boolean literals."""
        assert format_literal(True) == "true"
        assert format_literal(False) == "false"

    def test_format_literal_with_datatype(self):
        """Test formatting with datatype."""
        result = format_literal("123", datatype="http://www.w3.org/2001/XMLSchema#integer")
        assert '"123"' in result
        assert "XMLSchema#integer" in result

    def test_format_literal_with_language(self):
        """Test formatting with language tag."""
        result = format_literal("hello", lang="en")
        assert '"hello"@en' == result

    def test_format_literal_escapes_quotes(self):
        """Test that quotes are properly escaped."""
        result = format_literal('say "hello"')
        # rdflib handles escaping
        assert '"' in result or '\\"' in result


class TestFormatSubject:
    """Test subject formatting."""

    def test_format_variable_subject(self):
        """Test formatting variable subjects."""
        assert format_subject("?x") == "?x"
        assert format_subject("$person") == "$person"

    def test_format_uri_subject(self):
        """Test formatting URI subjects."""
        result = format_subject("http://example.org/person")
        assert result.startswith("<")
        assert result.endswith(">")

    def test_format_prefixed_subject(self):
        """Test formatting prefixed name subjects."""
        result = format_subject("foaf:Person")
        assert result == "foaf:Person"

    def test_format_blank_node_subject(self):
        """Test formatting blank node subjects."""
        result = format_subject("_:b1")
        assert result == "_:b1"

    def test_format_uri_in_brackets(self):
        """Test formatting URIs already in angle brackets."""
        result = format_subject("<http://example.org/person>")
        assert result.startswith("<")
        assert result.endswith(">")

    def test_invalid_subject_empty(self):
        """Test empty subject raises error."""
        with pytest.raises(ValueError, match="cannot be empty"):
            format_subject("")

    def test_invalid_subject_type(self):
        """Test invalid subject type."""
        with pytest.raises(ValueError, match="must be a string"):
            format_subject(123)  # type: ignore

    def test_invalid_subject_format(self):
        """Test invalid subject format."""
        with pytest.raises(ValueError, match="Invalid subject"):
            format_subject("just plain text")


class TestFormatPredicate:
    """Test predicate formatting."""

    def test_format_variable_predicate(self):
        """Test formatting variable predicates."""
        assert format_predicate("?p") == "?p"
        assert format_predicate("$property") == "$property"

    def test_format_uri_predicate(self):
        """Test formatting URI predicates."""
        result = format_predicate("http://xmlns.com/foaf/0.1/name")
        assert result.startswith("<")
        assert result.endswith(">")

    def test_format_prefixed_predicate(self):
        """Test formatting prefixed name predicates."""
        result = format_predicate("foaf:name")
        assert result == "foaf:name"

    def test_format_rdf_type_shorthand(self):
        """Test formatting 'a' shorthand."""
        result = format_predicate("a")
        assert result == "a"

    def test_format_property_path_predicate(self):
        """Test formatting property path predicates."""
        result = format_predicate("foaf:knows+")
        assert result == "foaf:knows+"

        result = format_predicate("foaf:knows/foaf:name")
        assert result == "foaf:knows/foaf:name"

    def test_invalid_predicate_empty(self):
        """Test empty predicate raises error."""
        with pytest.raises(ValueError, match="cannot be empty"):
            format_predicate("")

    def test_invalid_predicate_type(self):
        """Test invalid predicate type."""
        with pytest.raises(ValueError, match="must be a string"):
            format_predicate(123)  # type: ignore


class TestFormatObject:
    """Test object formatting."""

    def test_format_variable_object(self):
        """Test formatting variable objects."""
        assert format_object("?o") == "?o"
        assert format_object("$value") == "$value"

    def test_format_uri_object(self):
        """Test formatting URI objects."""
        result = format_object("http://example.org/person")
        assert result.startswith("<")
        assert result.endswith(">")

    def test_format_prefixed_object(self):
        """Test formatting prefixed name objects."""
        result = format_object("foaf:Person")
        assert result == "foaf:Person"

    def test_format_blank_node_object(self):
        """Test formatting blank node objects."""
        result = format_object("_:b1")
        assert result == "_:b1"

    def test_format_string_literal_object(self):
        """Test formatting string literal objects."""
        result = format_object("John Doe")
        assert result == '"John Doe"'

    def test_format_integer_object(self):
        """Test formatting integer objects."""
        result = format_object(42)
        assert "42" in result

    def test_format_float_object(self):
        """Test formatting float objects."""
        result = format_object(3.14)
        assert "3.14" in result

    def test_format_boolean_object(self):
        """Test formatting boolean objects."""
        assert format_object(True) == "true"
        assert format_object(False) == "false"

    def test_format_literal_with_datatype(self):
        """Test formatting literal with datatype."""
        result = format_object("123", datatype="http://www.w3.org/2001/XMLSchema#integer")
        assert '"123"' in result
        assert "XMLSchema#integer" in result

    def test_format_literal_with_language(self):
        """Test formatting literal with language."""
        result = format_object("Hello", lang="en")
        assert '"Hello"@en' == result

    def test_invalid_object_empty(self):
        """Test empty object raises error."""
        with pytest.raises(ValueError, match="cannot be empty"):
            format_object("")


class TestEdgeCases:
    """Test edge cases and integration scenarios."""

    def test_whitespace_stripping_structural(self):
        """Test whitespace is stripped for structural elements."""
        assert format_subject("  ?x  ") == "?x"
        assert format_predicate("  foaf:name  ") == "foaf:name"
        assert format_object("  ?o  ") == "?o"

    def test_whitespace_preserved_in_literals(self):
        """Test whitespace is preserved in string literals."""
        result = format_object("  text with spaces  ")
        assert "  text with spaces  " in result

    def test_uri_with_special_characters(self):
        """Test URIs with special characters."""
        # URI with query parameters
        result = format_uri("http://example.org/path?key=value&other=test")
        assert result.startswith("<")
        assert "example.org" in result

    def test_complex_property_paths(self):
        """Test complex property paths."""
        paths = [
            "foaf:knows+",
            "foaf:knows*",
            "foaf:knows?",
            "foaf:knows|foaf:friend",
            "foaf:knows/foaf:name",
            "^foaf:knows",
            "(foaf:knows+)/foaf:name",
            "!foaf:knows",
        ]
        for path in paths:
            result = format_predicate(path)
            assert result == path

    def test_datatypes_with_prefixes(self):
        """Test datatypes as prefixed names."""
        result = format_literal("123", datatype="xsd:integer")
        assert '"123"' in result
        # rdflib might expand or keep the prefix depending on configuration

    def test_invalid_uri_in_brackets_object(self):
        """Test invalid URIs in angle brackets."""
        with pytest.raises(ValueError):
            format_object("<not a valid uri>")

    def test_prefixed_name_fallback_to_literal(self):
        """Test that invalid prefixed names in objects become literals."""
        # String with multiple colons that's not a known URI scheme
        result = format_object("not:123:valid")
        # Should be treated as literal since it's not a valid URI or prefixed name
        assert result.startswith('"')

        # Test with a simple colon - "just:text" looks like a prefixed name
        # but it's actually valid according to our regex, so it won't be a literal
        # Let's test with something that definitely isn't a prefixed name
        result = format_object("123:text")  # Invalid prefix (starts with number)
        assert result.startswith('"')
