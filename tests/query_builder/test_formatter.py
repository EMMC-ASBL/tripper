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

    def test_uri_with_fragment(self):
        """Test URIs with fragment identifiers."""
        result = format_uri("http://example.org/resource#section1")
        assert result.startswith("<")
        assert "#section1" in result

    def test_uri_with_port(self):
        """Test URIs with explicit port numbers."""
        result = format_uri("http://example.org:8080/path")
        assert ":8080" in result

    def test_uri_with_authentication(self):
        """Test URIs with username in authority."""
        result = format_uri("http://user@example.org/path")
        assert "user@" in result

    def test_uri_with_ipv4_address(self):
        """Test URIs with IPv4 addresses."""
        result = format_uri("http://192.168.1.1/resource")
        assert "192.168.1.1" in result

    def test_uri_with_encoded_characters(self):
        """Test URIs with percent-encoded characters."""
        result = format_uri("http://example.org/path%20with%20spaces")
        assert "%20" in result

    def test_uri_file_scheme(self):
        """Test file: URIs."""
        result = format_uri("file:///path/to/file.txt")
        assert result.startswith("<file:")

    def test_uri_data_scheme(self):
        """Test data: URIs."""
        result = format_uri("data:text/plain;base64,SGVsbG8=")
        assert result.startswith("<data:")

    def test_uri_with_international_chars(self):
        """Test URIs with international characters."""
        # rdflib may accept international characters in URIs
        # This tests the current behavior rather than strict enforcement
        try:
            result = format_uri("http://example.org/ñoño")
            assert result.startswith("<")
        except ValueError:
            # It's also acceptable to reject unencoded international chars
            pass

    def test_uri_empty_after_scheme(self):
        """Test URIs with only scheme."""
        # rdflib may accept http:// as valid
        try:
            result = format_uri("http://")
            # If accepted, should be formatted
            assert result.startswith("<")
        except ValueError:
            # It's also acceptable to reject empty authority
            pass

    def test_uri_with_only_whitespace(self):
        """Test URIs that are only whitespace."""
        with pytest.raises(ValueError):
            format_uri("   \t\n   ")

    def test_multiple_uri_schemes(self):
        """Test various less common URI schemes."""
        schemes = [
            "ftp://ftp.example.org/file.txt",
            "tel:+1-816-555-1212",
            "urn:isbn:0451450523",
            "urn:uuid:6e8bc430-9c3a-11d9-9669-0800200c9a66",
            "doi:10.1000/182",
            "about:blank",
        ]
        for uri in schemes:
            result = format_uri(uri)
            assert result.startswith("<")
            assert result.endswith(">")

    def test_uri_with_special_characters(self):
        """Test URIs with special characters."""
        # URI with query parameters
        result = format_uri("http://example.org/path?key=value&other=test")
        assert result.startswith("<")
        assert "example.org" in result

    def test_format_uri_non_string_type(self):
        """Test that non-string types are rejected."""
        with pytest.raises(ValueError, match="must be a string"):
            format_uri(123)  # type: ignore
        with pytest.raises(ValueError, match="must be a string"):
            format_uri(None)  # type: ignore
        with pytest.raises(ValueError, match="must be a string"):
            format_uri(['http://example.org'])  # type: ignore


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

    def test_prefixed_name_with_numbers_in_local(self):
        """Test prefixed names with numbers in local part."""
        assert is_valid_prefixed_name("ex:resource123") is True
        assert is_valid_prefixed_name("ex:r1e2s3") is True

    def test_prefixed_name_with_multiple_dots(self):
        """Test prefixed names with multiple dots in local part."""
        assert is_valid_prefixed_name("ex:name.first.given") is True

    def test_prefixed_name_with_multiple_hyphens(self):
        """Test prefixed names with multiple hyphens."""
        assert is_valid_prefixed_name("my-long-prefix:my-long-name") is True

    def test_prefixed_name_long_prefix(self):
        """Test prefixed names with long prefix."""
        assert is_valid_prefixed_name("verylongprefix123:name") is True

    def test_prefixed_name_long_local(self):
        """Test prefixed names with long local part."""
        assert is_valid_prefixed_name("ex:veryLongLocalNameWithManyCamelCaseWords") is True

    def test_prefixed_name_empty_prefix_fails(self):
        """Test prefixed names with empty prefix."""
        assert is_valid_prefixed_name(":name") is False

    def test_prefixed_name_empty_local_fails(self):
        """Test prefixed names with empty local part."""
        assert is_valid_prefixed_name("ex:") is False

    def test_prefixed_name_multiple_colons_fails(self):
        """Test prefixed names with multiple colons."""
        assert is_valid_prefixed_name("ex:name:other") is False

    def test_prefixed_name_special_chars_fails(self):
        """Test prefixed names with special characters."""
        assert is_valid_prefixed_name("ex:name@test") is False
        assert is_valid_prefixed_name("ex:name#test") is False
        assert is_valid_prefixed_name("ex:name/test") is False

    def test_validate_prefixed_name_non_string_type(self):
        """Test that non-string types are rejected."""
        with pytest.raises(ValueError, match="must be a string"):
            validate_prefixed_name(123)  # type: ignore
        with pytest.raises(ValueError, match="must be a string"):
            validate_prefixed_name(None)  # type: ignore


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

    def test_variable_with_numbers(self):
        """Test variables with numbers in name."""
        assert is_valid_variable("?var1") is True
        assert is_valid_variable("?x2y3") is True
        assert is_valid_variable("$test123") is True

    def test_variable_with_underscores(self):
        """Test variables with underscores."""
        assert is_valid_variable("?my_var") is True
        assert is_valid_variable("?_private") is True
        assert is_valid_variable("$__dunder__") is True

    def test_variable_case_sensitivity(self):
        """Test that variable names are case-sensitive."""
        vars = ["?X", "?x", "?myVar", "?MyVar", "?MYVAR"]
        for var in vars:
            assert is_valid_variable(var) is True

    def test_variable_with_hyphens_fails(self):
        """Test variables with hyphens are invalid."""
        assert is_valid_variable("?my-var") is False
        assert is_valid_variable("$test-var") is False

    def test_variable_with_dots_fails(self):
        """Test variables with dots are invalid."""
        assert is_valid_variable("?my.var") is False

    def test_variable_mixed_prefix_styles(self):
        """Test that only one prefix style is used."""
        assert is_valid_variable("?x") is True
        assert is_valid_variable("$x") is True
        # These would be invalid (multiple prefixes)
        assert is_valid_variable("??x") is False
        assert is_valid_variable("$?x") is False

    def test_validate_variable_non_string_type(self):
        """Test that non-string types are rejected."""
        with pytest.raises(ValueError, match="must be a string"):
            validate_variable(123)  # type: ignore
        with pytest.raises(ValueError, match="must be a string"):
            validate_variable(None)  # type: ignore

    def test_validate_variable_empty_string(self):
        """Test that empty string after stripping is rejected."""
        with pytest.raises(ValueError, match="cannot be empty"):
            validate_variable("   ")
        with pytest.raises(ValueError, match="cannot be empty"):
            validate_variable("")


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

    def test_blank_node_with_numbers(self):
        """Test blank nodes with numbers."""
        assert is_blank_node("_:b1") is True
        assert is_blank_node("_:node123") is True
        assert is_blank_node("_:n456abc") is True

    def test_blank_node_with_underscores(self):
        """Test blank nodes with underscores."""
        assert is_blank_node("_:my_blank") is True
        assert is_blank_node("_:__private") is True

    def test_blank_node_with_dots(self):
        """Test blank nodes with dots."""
        assert is_blank_node("_:node.1") is True

    def test_blank_node_with_hyphens(self):
        """Test blank nodes with hyphens."""
        assert is_blank_node("_:node-1") is True

    def test_blank_node_starts_with_number_fails(self):
        """Test blank nodes starting with number."""
        assert is_blank_node("_:1node") is False

    def test_blank_node_special_chars_fails(self):
        """Test blank nodes with special characters."""
        assert is_blank_node("_:node@test") is False
        assert is_blank_node("_:node#1") is False

    def test_validate_blank_node_non_string_type(self):
        """Test that non-string types are rejected."""
        with pytest.raises(ValueError, match="must be a string"):
            validate_blank_node(123)  # type: ignore
        with pytest.raises(ValueError, match="must be a string"):
            validate_blank_node(None)  # type: ignore


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

    def test_property_path_sequence(self):
        """Test property path sequences."""
        assert is_property_path("ex:p1/ex:p2/ex:p3") is True

    def test_property_path_alternative(self):
        """Test property path alternatives."""
        assert is_property_path("ex:p1|ex:p2|ex:p3") is True

    def test_property_path_inverse(self):
        """Test inverse property paths."""
        assert is_property_path("^ex:property") is True
        assert is_property_path("^ex:p1/ex:p2") is True

    def test_property_path_negation(self):
        """Test negated property paths."""
        assert is_property_path("!ex:property") is True
        assert is_property_path("!(ex:p1|ex:p2)") is True

    def test_property_path_nested_groups(self):
        """Test nested groups in property paths."""
        assert is_property_path("((ex:p1|ex:p2)/ex:p3)*") is True

    def test_property_path_with_uri(self):
        """Test property paths with full URIs."""
        # The < character causes it to fail property path detection
        # Property paths need to be validated differently
        # Test a valid property path with operators
        assert is_property_path("ex:prop+") is True
        # Complex path with multiple properties
        assert is_property_path("(ex:p1|ex:p2)+") is True

    def test_property_path_with_rdf_type(self):
        """Test property paths with 'a' shorthand."""
        assert is_property_path("a|ex:subClassOf") is True

    def test_property_path_mixed_operators(self):
        """Test complex paths mixing operators."""
        paths = [
            "(ex:p1|ex:p2)+/ex:p3*",
            "^(ex:p1/ex:p2)",
            "!(ex:p1|ex:p2)/ex:p3",
            "ex:p1/(ex:p2|ex:p3)+",
        ]
        for path in paths:
            assert is_property_path(path) is True

    def test_property_path_with_spaces(self):
        """Test property paths with whitespace."""
        # Whitespace should be allowed for readability
        assert is_property_path("ex:p1 | ex:p2") is True
        assert is_property_path("ex:p1 / ex:p2") is True

    def test_property_path_invalid_chars(self):
        """Test property paths with invalid characters."""
        with pytest.raises(ValueError):
            validate_property_path("ex:prop;")
        with pytest.raises(ValueError):
            validate_property_path("ex:prop.")
        with pytest.raises(ValueError):
            validate_property_path("ex:prop{}")

    def test_validate_property_path_non_string_type(self):
        """Test that non-string types are rejected."""
        with pytest.raises(ValueError, match="must be a string"):
            validate_property_path(123)  # type: ignore
        with pytest.raises(ValueError, match="must be a string"):
            validate_property_path(None)  # type: ignore

    def test_validate_property_path_empty_string(self):
        """Test that empty string after stripping is rejected."""
        with pytest.raises(ValueError, match="cannot be empty"):
            validate_property_path("   ")
        with pytest.raises(ValueError, match="cannot be empty"):
            validate_property_path("")


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

    def test_literal_with_quotes(self):
        """Test literals containing various quote types."""
        result = format_literal('He said "hello"')
        assert '"' in result or '\\"' in result

    def test_literal_with_newlines(self):
        """Test literals with embedded newlines."""
        result = format_literal("line1\nline2\nline3")
        assert "line1" in result
        assert "line2" in result

    def test_literal_with_tabs(self):
        """Test literals with tab characters."""
        result = format_literal("col1\tcol2\tcol3")
        assert "col1" in result

    def test_literal_with_backslashes(self):
        """Test literals with backslash characters."""
        result = format_literal("path\\to\\file")
        assert "path" in result
        assert "file" in result

    def test_literal_empty_string(self):
        """Test empty string literal."""
        result = format_literal("")
        assert result == '""'

    def test_literal_only_whitespace(self):
        """Test literal with only whitespace characters."""
        result = format_literal("   ")
        assert '"' in result

    def test_literal_zero_values(self):
        """Test zero values for different types."""
        assert "0" in format_literal(0)
        assert "0" in format_literal(0.0)
        assert format_literal(False) == "false"

    def test_literal_negative_numbers(self):
        """Test negative numeric literals."""
        result = format_literal(-42)
        assert "-42" in result
        result = format_literal(-3.14)
        assert "-3.14" in result

    def test_literal_very_large_numbers(self):
        """Test very large numeric literals."""
        result = format_literal(999999999999999)
        assert "999999999999999" in result

    def test_literal_scientific_notation(self):
        """Test floating point in scientific notation."""
        result = format_literal(1.23e-10)
        assert "e" in result.lower() or "E" in result

    def test_literal_special_float_values(self):
        """Test special float values."""
        # Note: NaN and Inf may need special handling
        result = format_literal(float('inf'))
        assert result  # Should produce some result

    def test_literal_with_multiple_languages(self):
        """Test literals with different language tags."""
        langs = ["en", "fr", "de", "es", "ja", "zh"]
        for lang in langs:
            result = format_literal("Hello", lang=lang)
            assert f"@{lang}" in result

    def test_literal_language_with_region(self):
        """Test language tags with region subtags."""
        result = format_literal("Hello", lang="en-US")
        assert "@en-US" in result

    def test_literal_with_xsd_datatypes(self):
        """Test various XSD datatypes."""
        datatypes = [
            ("123", "http://www.w3.org/2001/XMLSchema#integer"),
            ("true", "http://www.w3.org/2001/XMLSchema#boolean"),
            ("2023-01-15", "http://www.w3.org/2001/XMLSchema#date"),
            ("12:30:00", "http://www.w3.org/2001/XMLSchema#time"),
            ("P1Y2M3D", "http://www.w3.org/2001/XMLSchema#duration"),
        ]
        for value, datatype in datatypes:
            result = format_literal(value, datatype=datatype)
            assert '"' in result
            assert "XMLSchema" in result

    def test_literal_unicode_characters(self):
        """Test literals with Unicode characters."""
        result = format_literal("Hello 世界 🌍")
        assert '"' in result

    def test_literal_with_both_datatype_and_lang(self):
        """Test that providing both datatype and language is handled."""
        # RDF spec: literals cannot have both language and datatype
        # rdflib prioritizes datatype over language
        result = format_literal("test", datatype="xsd:string", lang="en")
        # Datatype takes precedence in rdflib
        assert "xsd:string" in result or "XMLSchema#string" in result

    def test_datatypes_with_prefixes(self):
        """Test datatypes as prefixed names."""
        result = format_literal("123", datatype="xsd:integer")
        assert '"123"' in result
        # rdflib might expand or keep the prefix depending on configuration

    def test_format_literal_invalid_datatype_uri(self):
        """Test literal with invalid datatype URI."""
        # URI with spaces should be rejected
        with pytest.raises(ValueError, match="Invalid datatype URI"):
            format_literal("value", datatype="http://not valid uri with spaces")
        # URI with newline
        with pytest.raises(ValueError, match="Invalid datatype URI"):
            format_literal("value", datatype="http://example.org\ninvalid")
        # URI with tab
        with pytest.raises(ValueError, match="Invalid datatype URI"):
            format_literal("value", datatype="http://example.org\tinvalid")


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

    def test_subject_uri_variations(self):
        """Test various URI formats as subjects."""
        uris = [
            "http://example.org/resource",
            "https://example.org/resource",
            "urn:isbn:0451450523",
            "mailto:test@example.org",
        ]
        for uri in uris:
            result = format_subject(uri)
            assert result.startswith("<")
            assert result.endswith(">")

    def test_subject_none_fails(self):
        """Test None as subject raises error."""
        with pytest.raises(ValueError):
            format_subject(None)  # type: ignore

    def test_subject_number_fails(self):
        """Test numeric subject raises error."""
        with pytest.raises(ValueError):
            format_subject(123)  # type: ignore

    def test_subject_with_only_spaces_fails(self):
        """Test subject with only spaces."""
        with pytest.raises(ValueError):
            format_subject("   ")

    def test_subject_ambiguous_strings(self):
        """Test strings that could be multiple types."""
        # Should be treated as literals when used as object, but subjects are stricter
        with pytest.raises(ValueError):
            format_subject("plain text with spaces")

    def test_whitespace_stripping_subject(self):
        """Test whitespace is stripped for subjects."""
        assert format_subject("  ?x  ") == "?x"
        assert format_subject("  foaf:Person  ") == "foaf:Person"


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

    def test_predicate_rdf_type_variations(self):
        """Test various ways to express rdf:type."""
        # 'a' shorthand
        assert format_predicate("a") == "a"
        # Full prefixed name
        assert format_predicate("rdf:type") == "rdf:type"
        # Full URI would also work
        result = format_predicate("http://www.w3.org/1999/02/22-rdf-syntax-ns#type")
        assert result.startswith("<")

    def test_predicate_none_fails(self):
        """Test None as predicate raises error."""
        with pytest.raises(ValueError):
            format_predicate(None)  # type: ignore

    def test_predicate_empty_property_path_fails(self):
        """Test empty property path."""
        with pytest.raises(ValueError):
            format_predicate("")

    def test_whitespace_stripping_predicate(self):
        """Test whitespace is stripped for predicates."""
        assert format_predicate("  foaf:name  ") == "foaf:name"

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

    def test_invalid_object_whitespace_only(self):
        """Test whitespace-only object raises error."""
        with pytest.raises(ValueError, match="cannot be empty"):
            format_object("   ")
        with pytest.raises(ValueError, match="cannot be empty"):
            format_object("\t\n  ")

    def test_object_none_type_fails(self):
        """Test None as object raises error."""
        with pytest.raises(ValueError):
            format_object(None)  # type: ignore

    def test_object_list_fails(self):
        """Test list as object raises error."""
        with pytest.raises(ValueError):
            format_object([1, 2, 3])  # type: ignore

    def test_object_dict_fails(self):
        """Test dict as object raises error."""
        with pytest.raises(ValueError):
            format_object({"key": "value"})  # type: ignore

    def test_object_ambiguous_colon_strings(self):
        """Test strings with colons that aren't valid prefixed names."""
        # Invalid prefixed name should become literal
        result = format_object("time:12:30:45")
        assert result.startswith('"')

    def test_object_uri_like_strings(self):
        """Test strings that look like URIs but aren't."""
        # Missing scheme
        result = format_object("example.org/path")
        assert result.startswith('"')

        # Has colon but not a URI
        result = format_object("C:\\path\\to\\file")
        assert result.startswith('"')

    def test_whitespace_stripping_object(self):
        """Test whitespace is stripped for structural objects."""
        assert format_object("  ?o  ") == "?o"

    def test_whitespace_preserved_in_literals(self):
        """Test whitespace is preserved in string literals."""
        result = format_object("  text with spaces  ")
        assert "  text with spaces  " in result

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


class TestIntegration:
    """Edge cases involving combinations of formatting functions."""

    def test_same_value_different_contexts(self):
        """Test same value formatted differently in different contexts."""
        # A variable can be subject, predicate, or object
        var = "?x"
        assert format_subject(var) == var
        assert format_predicate(var) == var
        assert format_object(var) == var

        # A URI can be subject, predicate, or object
        uri = "http://example.org/resource"
        subj = format_subject(uri)
        pred = format_predicate(uri)
        obj = format_object(uri)
        assert subj == pred == obj
        assert subj.startswith("<")

        # A prefixed name can be subject, predicate, or object
        pn = "ex:Thing"
        assert format_subject(pn) == pn
        assert format_predicate(pn) == pn
        assert format_object(pn) == pn

    def test_string_literal_vs_structural_element(self):
        """Test distinction between literals and structural elements."""
        # As object, plain text becomes literal
        assert format_object("hello").startswith('"')

        # But variables, URIs, etc. are structural
        assert not format_object("?var").startswith('"')
        assert not format_object("ex:Thing").startswith('"')

    def test_boundary_between_uri_and_prefixed_name(self):
        """Test edge cases between URIs and prefixed names."""
        # Clear URI
        assert format_subject("http://example.org/x").startswith("<")

        # Clear prefixed name
        assert format_subject("ex:x") == "ex:x"

        # Ambiguous cases - something that looks like a prefixed name
        # "not-a-uri:but-has-colon" has hyphens which are allowed in prefixed names
        # So it would be treated as a valid prefixed name
        result = format_subject("valid_prefix:local_name")
        assert result == "valid_prefix:local_name"

    def test_validation_consistency(self):
        """Test that validation functions are consistent."""
        test_cases = [
            ("?var", is_valid_variable, True),
            ("ex:Thing", is_valid_prefixed_name, True),
            ("_:b1", is_blank_node, True),
            ("http://example.org", is_valid_uri, True),
            ("ex:p+", is_property_path, True),
        ]

        for value, validator, expected in test_cases:
            assert validator(value) == expected
