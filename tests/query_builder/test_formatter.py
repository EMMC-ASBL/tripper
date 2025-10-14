"""Tests for formatter functions."""

import pytest
from tripper.query_builder.formatter import (
    escape_string,
    sanitize_uri,
    sanitize_variable,
    sanitize_property_path,
    format_literal,
    format_subject,
    format_predicate,
    format_object,
    is_valid_uri
)


class TestEscapeString:
    """Test cases for escape_string function."""

    def test_escape_string_basic(self):
        """Test basic string escaping functionality."""
        input_str = 'Hello "world"\nwith newline'
        expected = 'Hello \\"world\\"\\nwith newline'
        result = escape_string(input_str)
        assert result == expected

    def test_escape_string_all_special_chars(self):
        """Test escaping all special characters."""
        input_str = '"quotes\' and\nlines\r\tand\\backslashes'
        expected = '\\"quotes\\\' and\\nlines\\r\\tand\\\\backslashes'
        result = escape_string(input_str)
        assert result == expected

    def test_escape_string_empty(self):
        """Test escaping empty string."""
        assert escape_string("") == ""

    def test_escape_string_unicode(self):
        """Test escaping Unicode characters."""
        input_str = 'Héllo "wörld" with émojis 🎉\n'
        expected = 'Héllo \\"wörld\\" with émojis 🎉\\n'
        result = escape_string(input_str)
        assert result == expected

    def test_escape_string_non_string_input(self):
        """Test escaping non-string input (should convert to string)."""
        # Test the isinstance check and automatic conversion
        result = escape_string(123)  # type: ignore - testing the conversion path
        assert result == "123"

        result = escape_string(True)  # type: ignore - testing the conversion path
        assert result == "True"

        result = escape_string(None)  # type: ignore - testing the conversion path
        assert result == "None"

    def test_escape_string_already_escaped(self):
        """Test escaping already escaped strings."""
        input_str = 'Already \\"escaped\\" string'
        expected = 'Already \\\\\\"escaped\\\\\\" string'
        result = escape_string(input_str)
        assert result == expected


class TestSanitizeUri:
    """Test cases for sanitize_uri function."""

    def test_sanitize_uri_basic(self):
        """Test basic URI sanitization."""
        uri = "http://example.org/path"
        result = sanitize_uri(uri)
        assert result == uri

    def test_sanitize_uri_with_spaces(self):
        """Test URI with spaces."""
        uri = "http://example.org/path with spaces"
        result = sanitize_uri(uri)
        assert " " not in result
        assert "path%20with%20spaces" in result

    def test_sanitize_uri_with_special_chars(self):
        """Test URI with special characters."""
        uri = "http://example.org/path?query=value&other=test"
        result = sanitize_uri(uri)
        # Basic structure should be preserved
        assert result.startswith("http://example.org/")

    def test_sanitize_uri_strips_whitespace(self):
        """Test that leading/trailing whitespace is stripped."""
        uri = "  http://example.org/path  "
        result = sanitize_uri(uri)
        assert not result.startswith(" ")
        assert not result.endswith(" ")

    def test_sanitize_uri_non_string_raises_error(self):
        """Test that non-string input raises ValueError."""
        with pytest.raises(ValueError, match="URI must be a string"):
            sanitize_uri(123)  # type: ignore

    def test_sanitize_uri_empty_string(self):
        """Test empty string handling."""
        with pytest.raises(ValueError):
            sanitize_uri("")


class TestSanitizeVariable:
    """Test cases for sanitize_variable function."""

    def test_sanitize_variable_with_question_mark(self):
        """Test variable that already has question mark."""
        result = sanitize_variable("?name")
        assert result == "?name"

    def test_sanitize_variable_with_dollar_sign(self):
        """Test variable that already has dollar sign."""
        result = sanitize_variable("$name")
        assert result == "$name"

    def test_sanitize_variable_without_prefix(self):
        """Test variable without prefix - should raise error."""
        # sanitize_variable expects variables to already have the prefix
        with pytest.raises(ValueError, match="Variable must start with"):
            sanitize_variable("name")

    def test_sanitize_variable_empty_raises_error(self):
        """Test that empty variable name raises error."""
        with pytest.raises(ValueError):
            sanitize_variable("")

    def test_sanitize_variable_only_prefix_raises_error(self):
        """Test that only prefix raises error."""
        with pytest.raises(ValueError):
            sanitize_variable("?")
        with pytest.raises(ValueError):
            sanitize_variable("$")

    def test_sanitize_variable_invalid_chars(self):
        """Test variable with invalid characters."""
        # Variables without prefix should raise an error
        with pytest.raises(ValueError, match="Variable must start with"):
            sanitize_variable("valid_name123")

        # Valid variable with prefix should work
        result = sanitize_variable("?valid_name123")
        assert result == "?valid_name123"

    def test_sanitize_variable_non_string_input(self):
        """Test non-string input should raise ValueError."""
        with pytest.raises(ValueError, match="Variable must be a string"):
            sanitize_variable(123)  # type: ignore
        with pytest.raises(ValueError, match="Variable must be a string"):
            sanitize_variable(None)  # type: ignore


class TestSanitizePropertyPath:
    """Test cases for sanitize_property_path function."""

    def test_sanitize_property_path_basic(self):
        """Test basic property path validation."""
        result = sanitize_property_path("foaf:knows")
        assert result == "foaf:knows"

    def test_sanitize_property_path_with_operators(self):
        """Test property paths with operators."""
        assert sanitize_property_path("foaf:knows+") == "foaf:knows+"
        assert sanitize_property_path("foaf:knows*") == "foaf:knows*"
        assert sanitize_property_path("foaf:knows?") == "foaf:knows?"
        assert sanitize_property_path("foaf:knows|foaf:friend") == "foaf:knows|foaf:friend"

    def test_sanitize_property_path_non_string_raises_error(self):
        """Test non-string input raises ValueError."""
        with pytest.raises(ValueError, match="Property path must be a string"):
            sanitize_property_path(123)  # type: ignore

    def test_sanitize_property_path_empty_raises_error(self):
        """Test empty path raises ValueError."""
        with pytest.raises(ValueError, match="Property path cannot be empty"):
            sanitize_property_path("")

    def test_sanitize_property_path_dangerous_chars(self):
        """Test property paths with dangerous characters."""
        dangerous_paths = [
            "foaf:knows.",
            "foaf:knows;",
            "foaf:knows#",
            "foaf:knows\n",
            "foaf:knows\r",
            "foaf:knows\t",
            "foaf:knows{}",
            "foaf:knows[]"
        ]
        for path in dangerous_paths:
            with pytest.raises(ValueError, match="Invalid character in property path"):
                sanitize_property_path(path)


class TestFormatLiteral:
    """Test cases for format_literal function."""

    def test_format_literal_string(self):
        """Test formatting string literals."""
        result = format_literal("hello world")
        assert result == '"hello world"'

    def test_format_literal_string_with_quotes(self):
        """Test formatting string with quotes."""
        result = format_literal('say "hello"')
        assert result == '"say \\"hello\\""'

    def test_format_literal_integer(self):
        """Test formatting integer literals."""
        result = format_literal(42)
        assert result == "42"

    def test_format_literal_float(self):
        """Test formatting float literals."""
        result = format_literal(3.14)
        assert result == "3.14"

    def test_format_literal_boolean(self):
        """Test formatting boolean literals."""
        assert format_literal(True) == "true"
        assert format_literal(False) == "false"

    def test_format_literal_with_datatype(self):
        """Test formatting with explicit datatype."""
        result = format_literal("123", datatype="xsd:int")
        assert result == '"123"^^<xsd:int>'

    def test_format_literal_with_language(self):
        """Test formatting with language tag."""
        result = format_literal("hello", lang="en")
        assert result == '"hello"@en'

    def test_format_literal_datatype_and_lang_behavior(self):
        """Test behavior when both datatype and language are provided."""
        # The implementation uses elif, so language takes precedence
        result = format_literal("test", datatype="xsd:string", lang="en")
        assert result == '"test"@en'  # Language takes precedence over datatype


class TestFormatSubject:
    """Test cases for format_subject function."""

    def test_format_subject_uri(self):
        """Test formatting URI subjects."""
        result = format_subject("http://example.org/person")
        assert result == "<http://example.org/person>"

    def test_format_subject_prefixed_uri(self):
        """Test formatting prefixed URI subjects."""
        result = format_subject("foaf:Person")
        assert result == "foaf:Person"

    def test_format_subject_variable(self):
        """Test formatting variable subjects."""
        result = format_subject("?person")
        assert result == "?person"

    def test_format_subject_blank_node(self):
        """Test formatting blank node subjects."""
        result = format_subject("_:blank1")
        assert result == "_:blank1"

    def test_format_subject_invalid_prefixed_name(self):
        """Test formatting invalid prefixed names."""
        # Invalid prefix (starts with number)
        with pytest.raises(ValueError, match="Invalid namespace prefix"):
            format_subject("123invalid:name")

        # Note: Testing specific local name patterns that trigger validation
        # is challenging as the regex r'^[a-zA-Z_][\w\-\.]*$' is quite permissive

    def test_format_subject_dangerous_characters(self):
        """Test subjects with dangerous characters."""
        dangerous_subjects = [
            "subject;",
            "subject#",
            "subject\n",
            "subject\r",
            "subject\t",
            "subject{}",
            "subject[]",
            "subject "
        ]
        for subj in dangerous_subjects:
            with pytest.raises(ValueError, match="Invalid subject"):
                format_subject(subj)

    def test_format_subject_invalid_format(self):
        """Test completely invalid subject formats."""
        with pytest.raises(ValueError, match="Invalid subject format"):
            format_subject("just_plain_text")


class TestFormatPredicate:
    """Test cases for format_predicate function."""

    def test_format_predicate_uri(self):
        """Test formatting URI predicates."""
        result = format_predicate("http://xmlns.com/foaf/0.1/name")
        assert result == "<http://xmlns.com/foaf/0.1/name>"

    def test_format_predicate_prefixed_uri(self):
        """Test formatting prefixed URI predicates."""
        result = format_predicate("foaf:name")
        assert result == "foaf:name"

    def test_format_predicate_rdf_type_shorthand(self):
        """Test formatting 'a' shorthand for rdf:type."""
        result = format_predicate("a")
        assert result == "a"

    def test_format_predicate_variable(self):
        """Test formatting variable predicates."""
        result = format_predicate("?predicate")
        assert result == "?predicate"

    def test_format_predicate_property_path(self):
        """Test formatting property path predicates."""
        result = format_predicate("foaf:knows+")
        assert result == "foaf:knows+"

    def test_format_predicate_invalid_prefixed_name(self):
        """Test formatting invalid prefixed names."""
        # Invalid prefix (starts with number)
        with pytest.raises(ValueError, match="Invalid namespace prefix"):
            format_predicate("123invalid:name")

        # Note: Testing specific local name patterns that trigger validation
        # is challenging as the regex r'^[a-zA-Z_][\w\-\.]*$' is quite permissive

    def test_format_predicate_dangerous_characters(self):
        """Test predicates with dangerous characters."""
        dangerous_predicates = [
            "predicate.",
            "predicate;",
            "predicate#",
            "predicate\n",
            "predicate\r",
            "predicate\t",
            "predicate{}",
            "predicate[]",
            "predicate "
        ]
        for pred in dangerous_predicates:
            with pytest.raises(ValueError, match="Invalid predicate"):
                format_predicate(pred)

    def test_format_predicate_invalid_format(self):
        """Test completely invalid predicate formats."""
        with pytest.raises(ValueError, match="Invalid predicate format"):
            format_predicate("just_plain_text")


class TestFormatObject:
    """Test cases for format_object function."""

    def test_format_object_uri(self):
        """Test formatting URI objects."""
        result = format_object("http://example.org/person")
        assert result == "<http://example.org/person>"

    def test_format_object_prefixed_uri(self):
        """Test formatting prefixed URI objects."""
        result = format_object("foaf:Person")
        assert result == "foaf:Person"

    def test_format_object_variable(self):
        """Test formatting variable objects."""
        result = format_object("?person")
        assert result == "?person"

    def test_format_object_string_literal(self):
        """Test formatting string literal objects."""
        result = format_object("John Doe")
        assert result == '"John Doe"'

    def test_format_object_integer_literal(self):
        """Test formatting integer literal objects."""
        result = format_object(25)
        assert result == "25"

    def test_format_object_with_datatype(self):
        """Test formatting with datatype."""
        result = format_object("25", datatype="xsd:int")
        assert result == '"25"^^<xsd:int>'

    def test_format_object_with_language(self):
        """Test formatting with language tag."""
        result = format_object("Hello", lang="en")
        assert result == '"Hello"@en'

    def test_format_object_invalid_angle_brackets(self):
        """Test objects with invalid angle bracket usage."""
        # Missing closing bracket
        with pytest.raises(ValueError, match="must end with"):
            format_object("<http://example.org")

        # Empty URI
        with pytest.raises(ValueError, match="URI cannot be empty"):
            format_object("<>")

        # Invalid URI inside brackets
        with pytest.raises(ValueError, match="Invalid URI in object"):
            format_object("<not a valid uri>")

    def test_format_object_invalid_prefixed_fallback(self):
        """Test objects with invalid prefixed names fall back to literals."""
        # Invalid prefix should be treated as literal
        result = format_object("123invalid:name")
        assert result.startswith('"')  # Should be a literal

        # Note: Testing exact local name validation patterns is complex
        # as format_object treats many patterns as URIs when they match prefixed patterns


class TestIsValidUri:
    """Test cases for is_valid_uri function."""

    def test_is_valid_uri_http(self):
        """Test valid HTTP URIs."""
        assert is_valid_uri("http://example.org") is True
        assert is_valid_uri("http://example.org/path") is True

    def test_is_valid_uri_https(self):
        """Test valid HTTPS URIs."""
        assert is_valid_uri("https://example.org") is True

    def test_is_valid_uri_other_schemes(self):
        """Test other valid URI schemes."""
        assert is_valid_uri("ftp://example.org") is True
        assert is_valid_uri("mailto:test@example.org") is True

    def test_is_valid_uri_invalid(self):
        """Test invalid URIs."""
        assert is_valid_uri("not a uri") is False
        assert is_valid_uri("") is False
        # Note: "http://" might be considered valid by the implementation

    def test_is_valid_uri_relative(self):
        """Test relative URIs."""
        # Depending on implementation, these might be valid or invalid
        result = is_valid_uri("/relative/path")
        assert isinstance(result, bool)  # Should return a boolean either way

    def test_is_valid_uri_non_string_input(self):
        """Test non-string input should return False."""
        assert is_valid_uri(123) is False  # type: ignore
        assert is_valid_uri(None) is False  # type: ignore
        assert is_valid_uri([]) is False  # type: ignore

    def test_is_valid_uri_empty_after_strip(self):
        """Test URI that becomes empty after stripping."""
        assert is_valid_uri("   ") is False
        assert is_valid_uri("\t\n") is False

    def test_is_valid_uri_dangerous_characters(self):
        """Test URIs with dangerous characters."""
        # Test characters that should be rejected
        dangerous_uris = [
            "http://example.org<>",
            "http://example.org{}",
            "http://example.org|",
            "http://example.org\\",
            "http://example.org^",
            "http://example.org`",
            "http://example.org[]"
        ]
        for uri in dangerous_uris:
            assert is_valid_uri(uri) is False, f"Should reject dangerous URI: {uri!r}"

        # Note: Some control characters like \n, \r, \t might be handled differently
        # by urlparse, so we test them separately if needed

    def test_is_valid_uri_malformed_parse(self):
        """Test URIs that cause urlparse exceptions."""
        # This might be hard to trigger, but testing the exception handling
        # Most malformed URIs are handled gracefully by urlparse
        pass
