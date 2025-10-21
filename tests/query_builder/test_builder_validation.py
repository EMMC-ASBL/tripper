"""Tests for builder input validation."""

import pytest
from tripper.query_builder.builder import SPARQLQuery


class TestAggregationValidation:
    """Test validation for aggregation functions."""

    def test_select_count_invalid_variable(self):
        """Test COUNT rejects invalid variable names."""
        query = SPARQLQuery()
        with pytest.raises(ValueError, match=r"Variable must start with '\?' or '\$'"):
            query.select_count("invalid", "?count")

    def test_select_count_invalid_alias(self):
        """Test COUNT rejects invalid alias names."""
        query = SPARQLQuery()
        with pytest.raises(ValueError, match=r"Variable must start with '\?' or '\$'"):
            query.select_count("?item", "count")

    def test_select_count_wildcard_valid(self):
        """Test COUNT accepts * wildcard."""
        query = SPARQLQuery().select_count("*", "?total")
        assert "(COUNT(*) AS ?total)" in query.build()

    def test_select_sum_invalid_variable(self):
        """Test SUM rejects invalid variable names."""
        query = SPARQLQuery()
        with pytest.raises(ValueError, match="Invalid variable name"):
            query.select_sum("?price$", "?total")

    def test_select_sum_invalid_alias(self):
        """Test SUM rejects invalid alias names."""
        query = SPARQLQuery()
        with pytest.raises(ValueError, match=r"Variable must start with '\?' or '\$'"):
            query.select_sum("?price", "total")

    def test_select_avg_invalid_variable(self):
        """Test AVG rejects invalid variable names."""
        query = SPARQLQuery()
        with pytest.raises(ValueError, match="Invalid variable name"):
            query.select_avg("?rating!", "?avg")

    def test_select_avg_invalid_alias(self):
        """Test AVG rejects invalid alias names."""
        query = SPARQLQuery()
        with pytest.raises(ValueError, match=r"Variable must start with '\?' or '\$'"):
            query.select_avg("?rating", "avg_rating")

    def test_select_min_invalid_variable(self):
        """Test MIN rejects invalid variable names."""
        query = SPARQLQuery()
        with pytest.raises(ValueError, match="Invalid variable name"):
            query.select_min("?price@", "?min")

    def test_select_min_invalid_alias(self):
        """Test MIN rejects invalid alias names."""
        query = SPARQLQuery()
        with pytest.raises(ValueError, match="Invalid variable name"):
            query.select_min("?price", "?min-price")

    def test_select_max_invalid_variable(self):
        """Test MAX rejects invalid variable names."""
        query = SPARQLQuery()
        with pytest.raises(ValueError, match="Invalid variable name"):
            query.select_max("?temp#", "?max")

    def test_select_max_invalid_alias(self):
        """Test MAX rejects invalid alias names."""
        query = SPARQLQuery()
        with pytest.raises(ValueError, match="Invalid variable name"):
            query.select_max("?temp", "?max.temp")

    def test_select_sample_invalid_variable(self):
        """Test SAMPLE rejects invalid variable names."""
        query = SPARQLQuery()
        with pytest.raises(ValueError, match="Invalid variable name"):
            query.select_sample("?member%", "?any")

    def test_select_sample_invalid_alias(self):
        """Test SAMPLE rejects invalid alias names."""
        query = SPARQLQuery()
        with pytest.raises(ValueError, match="Invalid variable name"):
            query.select_sample("?member", "?any member")

    def test_select_group_concat_invalid_variable(self):
        """Test GROUP_CONCAT rejects invalid variable names."""
        query = SPARQLQuery()
        with pytest.raises(ValueError, match="Invalid variable name"):
            query.select_group_concat("?name&", "?names")

    def test_select_group_concat_invalid_alias(self):
        """Test GROUP_CONCAT rejects invalid alias names."""
        query = SPARQLQuery()
        with pytest.raises(ValueError, match=r"Variable must start with '\?' or '\$'"):
            query.select_group_concat("?name", "names_list")

    def test_select_group_concat_empty_separator(self):
        """Test GROUP_CONCAT accepts empty separator."""
        query = SPARQLQuery().select_group_concat("?name", "?names", separator="")
        assert 'SEPARATOR=""' in query.build()

    def test_select_group_concat_special_char_separator(self):
        """Test GROUP_CONCAT with special characters in separator."""
        query = SPARQLQuery().select_group_concat("?name", "?names", separator="|")
        assert 'SEPARATOR="|"' in query.build()

    def test_select_group_concat_backslash_separator(self):
        """Test GROUP_CONCAT properly escapes backslash in separator."""
        query = SPARQLQuery().select_group_concat("?name", "?names", separator="\\")
        assert 'SEPARATOR="\\\\"' in query.build()

    def test_select_group_concat_quote_separator(self):
        """Test GROUP_CONCAT properly escapes quote in separator."""
        query = SPARQLQuery().select_group_concat("?name", "?names", separator='"')
        assert 'SEPARATOR="\\""' in query.build()


class TestSelectValidation:
    """Test validation for basic select functions."""

    def test_select_invalid_variable(self):
        """Test select rejects invalid variable names."""
        query = SPARQLQuery()
        with pytest.raises(ValueError, match=r"Variable must start with '\?' or '\$'"):
            query.select("invalid_var")

    def test_select_distinct_invalid_variable(self):
        """Test select_distinct rejects invalid variable names."""
        query = SPARQLQuery()
        with pytest.raises(ValueError, match=r"Variable must start with '\?' or '\$'"):
            query.select_distinct("no_question_mark")

    def test_select_reduced_invalid_variable(self):
        """Test select_reduced rejects invalid variable names."""
        query = SPARQLQuery()
        with pytest.raises(ValueError, match="Invalid variable name"):
            query.select_reduced("?var with space")


class TestGroupByValidation:
    """Test validation for GROUP BY clause."""

    def test_group_by_invalid_variable(self):
        """Test group_by rejects invalid variable names."""
        query = SPARQLQuery()
        with pytest.raises(ValueError, match=r"Variable must start with '\?' or '\$'"):
            query.group_by("category")

    def test_group_by_multiple_invalid(self):
        """Test group_by rejects invalid variables in multiple arguments."""
        query = SPARQLQuery()
        with pytest.raises(ValueError, match=r"Variable must start with '\?' or '\$'"):
            query.group_by("?valid", "invalid")


class TestOrderByValidation:
    """Test validation for ORDER BY clause."""

    def test_order_by_invalid_variable(self):
        """Test order_by rejects invalid variable names."""
        query = SPARQLQuery()
        with pytest.raises(ValueError, match=r"Variable must start with '\?' or '\$'"):
            query.order_by("name")

    def test_order_by_expression_allowed(self):
        """Test order_by allows expressions (not just variables)."""
        query = SPARQLQuery().select("?name").order_by("?name")
        assert "ORDER BY ?name" in query.build()
