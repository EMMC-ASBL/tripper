"""Tests for builder string generation."""

from tripper.query_builder import select, select_distinct, select_reduced


class TestBasicSelectQueries:
    """Test basic SELECT query variations."""

    def test_simple_select_query_string(self):
        """Test basic SELECT query string generation."""
        query = (
            select("?researcher", "?name")
            .prefix("ex", "http://example.org/")
            .where("?researcher", "a", "ex:Researcher")
            .where("?researcher", "foaf:name", "?name")
        )

        result = query.build()

        # Expected SPARQL string (normalized for comparison)
        expected_lines = [
            "PREFIX ex: <http://example.org/>",
            "",
            "SELECT ?researcher ?name",
            "WHERE {",
            "  ?researcher a ex:Researcher .",
            "  ?researcher foaf:name ?name .",
            "}"
        ]
        expected = "\n".join(expected_lines)

        assert result == expected

    def test_select_distinct_query_string(self):
        """Test SELECT DISTINCT query string generation."""
        query = (
            select_distinct("?university")
            .prefix("ex", "http://example.org/")
            .where("?researcher", "ex:affiliatedWith", "?university")
        )

        result = query.build()

        expected_lines = [
            "PREFIX ex: <http://example.org/>",
            "",
            "SELECT DISTINCT ?university",
            "WHERE {",
            "  ?researcher ex:affiliatedWith ?university .",
            "}"
        ]
        expected = "\n".join(expected_lines)

        assert result == expected

    def test_select_reduced_query_string(self):
        """Test SELECT REDUCED query string generation."""
        query = (
            select_reduced("?journal")
            .prefix("ex", "http://example.org/")
            .where("?paper", "ex:publishedIn", "?journal")
        )

        result = query.build()

        expected_lines = [
            "PREFIX ex: <http://example.org/>",
            "",
            "SELECT REDUCED ?journal",
            "WHERE {",
            "  ?paper ex:publishedIn ?journal .",
            "}"
        ]
        expected = "\n".join(expected_lines)

        assert result == expected

    def test_multiple_prefixes(self):
        """Test query with multiple prefixes."""
        query = (
            select("?person", "?name", "?email")
            .prefix("foaf", "http://xmlns.com/foaf/0.1/")
            .prefix("ex", "http://example.org/")
            .prefix("dc", "http://purl.org/dc/elements/1.1/")
            .where("?person", "a", "foaf:Person")
            .where("?person", "foaf:name", "?name")
            .where("?person", "foaf:mbox", "?email")
        )

        result = query.build()

        expected_lines = [
            "PREFIX foaf: <http://xmlns.com/foaf/0.1/>",
            "PREFIX ex: <http://example.org/>",
            "PREFIX dc: <http://purl.org/dc/elements/1.1/>",
            "",
            "SELECT ?person ?name ?email",
            "WHERE {",
            "  ?person a foaf:Person .",
            "  ?person foaf:name ?name .",
            "  ?person foaf:mbox ?email .",
            "}"
        ]
        expected = "\n".join(expected_lines)

        assert result == expected


class TestFromClauses:
    """Test FROM and FROM NAMED clauses."""

    def test_from_graph(self):
        """Test FROM clause generation."""
        query = (
            select("?researcher", "?name")
            .prefix("ex", "http://example.org/")
            .from_graph("http://example.org/research-data")
            .where("?researcher", "a", "ex:Researcher")
            .where("?researcher", "foaf:name", "?name")
        )

        result = query.build()

        expected_lines = [
            "PREFIX ex: <http://example.org/>",
            "",
            "SELECT ?researcher ?name",
            "FROM <http://example.org/research-data>",
            "WHERE {",
            "  ?researcher a ex:Researcher .",
            "  ?researcher foaf:name ?name .",
            "}"
        ]
        expected = "\n".join(expected_lines)

        assert result == expected

    def test_from_named_graph(self):
        """Test FROM NAMED clause generation."""
        query = (
            select("?researcher", "?name")
            .prefix("ex", "http://example.org/")
            .from_named_graph("http://example.org/metadata")
            .where("?researcher", "a", "ex:Researcher")
            .where("?researcher", "foaf:name", "?name")
        )

        result = query.build()

        expected_lines = [
            "PREFIX ex: <http://example.org/>",
            "",
            "SELECT ?researcher ?name",
            "FROM NAMED <http://example.org/metadata>",
            "WHERE {",
            "  ?researcher a ex:Researcher .",
            "  ?researcher foaf:name ?name .",
            "}"
        ]
        expected = "\n".join(expected_lines)

        assert result == expected

    def test_multiple_from_clauses(self):
        """Test multiple FROM and FROM NAMED clauses."""
        query = (
            select("?researcher", "?name")
            .prefix("ex", "http://example.org/")
            .from_graph("http://example.org/main-data")
            .from_graph("http://example.org/backup-data")
            .from_named_graph("http://example.org/metadata")
            .from_named_graph("http://example.org/provenance")
            .where("?researcher", "a", "ex:Researcher")
        )

        result = query.build()

        expected_lines = [
            "PREFIX ex: <http://example.org/>",
            "",
            "SELECT ?researcher ?name",
            "FROM <http://example.org/main-data>",
            "FROM <http://example.org/backup-data>",
            "FROM NAMED <http://example.org/metadata>",
            "FROM NAMED <http://example.org/provenance>",
            "WHERE {",
            "  ?researcher a ex:Researcher .",
            "}"
        ]
        expected = "\n".join(expected_lines)

        assert result == expected


class TestOptionalClauses:
    """Test OPTIONAL pattern generation."""

    def test_simple_optional(self):
        """Test basic OPTIONAL clause."""

        def add_optional_email(q):
            q.where("?researcher", "foaf:mbox", "?email")

        query = (
            select("?researcher", "?name", "?email")
            .prefix("ex", "http://example.org/")
            .where("?researcher", "a", "ex:Researcher")
            .where("?researcher", "foaf:name", "?name")
            .optional(add_optional_email)
        )

        result = query.build()

        expected_lines = [
            "PREFIX ex: <http://example.org/>",
            "",
            "SELECT ?researcher ?name ?email",
            "WHERE {",
            "  ?researcher a ex:Researcher .",
            "  ?researcher foaf:name ?name .",
            "  OPTIONAL {",
            "    ?researcher foaf:mbox ?email .",
            "  }",
            "}"
        ]
        expected = "\n".join(expected_lines)

        assert result == expected

    def test_multiple_optional_patterns(self):
        """Test multiple OPTIONAL clauses."""
        query = (
            select("?researcher", "?name", "?email", "?phone")
            .prefix("ex", "http://example.org/")
            .where("?researcher", "a", "ex:Researcher")
            .where("?researcher", "foaf:name", "?name")
            .optional(lambda q: q.where("?researcher", "foaf:mbox", "?email"))
            .optional(lambda q: q.where("?researcher", "foaf:phone", "?phone"))
        )

        result = query.build()

        expected_lines = [
            "PREFIX ex: <http://example.org/>",
            "",
            "SELECT ?researcher ?name ?email ?phone",
            "WHERE {",
            "  ?researcher a ex:Researcher .",
            "  ?researcher foaf:name ?name .",
            "  OPTIONAL {",
            "    ?researcher foaf:mbox ?email .",
            "  }",
            "  OPTIONAL {",
            "    ?researcher foaf:phone ?phone .",
            "  }",
            "}"
        ]
        expected = "\n".join(expected_lines)

        assert result == expected

    def test_nested_optional_patterns(self):
        """Test OPTIONAL with multiple triples."""
        query = (
            select("?researcher", "?name", "?university", "?department")
            .prefix("ex", "http://example.org/")
            .where("?researcher", "a", "ex:Researcher")
            .where("?researcher", "foaf:name", "?name")
            .optional(lambda q: (
                q.where("?researcher", "ex:affiliatedWith", "?university")
                .where("?university", "ex:hasDepartment", "?department")
            ))
        )

        result = query.build()

        expected_lines = [
            "PREFIX ex: <http://example.org/>",
            "",
            "SELECT ?researcher ?name ?university ?department",
            "WHERE {",
            "  ?researcher a ex:Researcher .",
            "  ?researcher foaf:name ?name .",
            "  OPTIONAL {",
            "    ?researcher ex:affiliatedWith ?university .",
            "    ?university ex:hasDepartment ?department .",
            "  }",
            "}"
        ]
        expected = "\n".join(expected_lines)

        assert result == expected


class TestUnionClauses:
    """Test UNION pattern generation."""

    def test_simple_union(self):
        """Test basic UNION clause."""
        query = (
            select("?person", "?name")
            .prefix("ex", "http://example.org/")
            .union(
                lambda q: q.where("?person", "a", "ex:Researcher").where("?person", "foaf:name", "?name"),
                lambda q: q.where("?person", "a", "ex:Student").where("?person", "foaf:name", "?name")
            )
        )

        result = query.build()

        expected_lines = [
            "PREFIX ex: <http://example.org/>",
            "",
            "SELECT ?person ?name",
            "WHERE {",
            "  {",
            "    ?person a ex:Researcher .",
            "    ?person foaf:name ?name .",
            "  }",
            "  UNION",
            "  {",
            "    ?person a ex:Student .",
            "    ?person foaf:name ?name .",
            "  }",
            "}"
        ]
        expected = "\n".join(expected_lines)

        assert result == expected

    def test_triple_union(self):
        """Test UNION with three alternatives."""
        query = (
            select("?person", "?type")
            .prefix("ex", "http://example.org/")
            .union(
                lambda q: q.where("?person", "a", "ex:Researcher").where("?person", "ex:type", "researcher"),
                lambda q: q.where("?person", "a", "ex:Student").where("?person", "ex:type", "student"),
                lambda q: q.where("?person", "a", "ex:Staff").where("?person", "ex:type", "staff")
            )
        )

        result = query.build()

        expected_lines = [
            "PREFIX ex: <http://example.org/>",
            "",
            "SELECT ?person ?type",
            "WHERE {",
            "  {",
            "    ?person a ex:Researcher .",
            '    ?person ex:type "researcher" .',
            "  }",
            "  UNION",
            "  {",
            "    ?person a ex:Student .",
            '    ?person ex:type "student" .',
            "  }",
            "  UNION",
            "  {",
            "    ?person a ex:Staff .",
            '    ?person ex:type "staff" .',
            "  }",
            "}"
        ]
        expected = "\n".join(expected_lines)

        assert result == expected

    def test_union_with_common_patterns(self):
        """Test UNION combined with common WHERE patterns."""
        query = (
            select("?person", "?name", "?role")
            .prefix("ex", "http://example.org/")
            .where("?person", "foaf:name", "?name")
            .union(
                lambda q: q.where("?person", "a", "ex:Researcher").where("?person", "ex:role", "?role"),
                lambda q: q.where("?person", "a", "ex:Student").where("?person", "ex:role", "?role")
            )
        )

        result = query.build()

        expected_lines = [
            "PREFIX ex: <http://example.org/>",
            "",
            "SELECT ?person ?name ?role",
            "WHERE {",
            "  ?person foaf:name ?name .",
            "  {",
            "    ?person a ex:Researcher .",
            "    ?person ex:role ?role .",
            "  }",
            "  UNION",
            "  {",
            "    ?person a ex:Student .",
            "    ?person ex:role ?role .",
            "  }",
            "}"
        ]
        expected = "\n".join(expected_lines)

        assert result == expected


class TestMinusAndGraph:
    """Test MINUS and GRAPH pattern generation."""

    def test_minus_clause(self):
        """Test MINUS clause generation."""
        query = (
            select("?researcher", "?name")
            .prefix("ex", "http://example.org/")
            .where("?researcher", "a", "ex:Researcher")
            .where("?researcher", "foaf:name", "?name")
            .minus(lambda q: q.where("?researcher", "ex:status", "ex:inactive"))
        )

        result = query.build()

        expected_lines = [
            "PREFIX ex: <http://example.org/>",
            "",
            "SELECT ?researcher ?name",
            "WHERE {",
            "  ?researcher a ex:Researcher .",
            "  ?researcher foaf:name ?name .",
            "  MINUS {",
            "    ?researcher ex:status ex:inactive .",
            "  }",
            "}"
        ]
        expected = "\n".join(expected_lines)

        assert result == expected

    def test_graph_clause(self):
        """Test GRAPH clause generation."""
        query = (
            select("?researcher", "?name")
            .prefix("ex", "http://example.org/")
            .graph("?g", lambda q: (
                q.where("?researcher", "a", "ex:Researcher")
                .where("?researcher", "foaf:name", "?name")
            ))
        )

        result = query.build()

        expected_lines = [
            "PREFIX ex: <http://example.org/>",
            "",
            "SELECT ?researcher ?name",
            "WHERE {",
            "  GRAPH ?g {",
            "    ?researcher a ex:Researcher .",
            "    ?researcher foaf:name ?name .",
            "  }",
            "}"
        ]
        expected = "\n".join(expected_lines)

        assert result == expected

    def test_named_graph_clause(self):
        """Test GRAPH clause with specific graph URI."""
        query = (
            select("?researcher", "?name")
            .prefix("ex", "http://example.org/")
            .graph("http://example.org/metadata", lambda q: (
                q.where("?researcher", "a", "ex:Researcher")
                .where("?researcher", "foaf:name", "?name")
            ))
        )

        result = query.build()

        expected_lines = [
            "PREFIX ex: <http://example.org/>",
            "",
            "SELECT ?researcher ?name",
            "WHERE {",
            "  GRAPH <http://example.org/metadata> {",
            "    ?researcher a ex:Researcher .",
            "    ?researcher foaf:name ?name .",
            "  }",
            "}"
        ]
        expected = "\n".join(expected_lines)

        assert result == expected


class TestFilterClauses:
    """Test FILTER pattern generation."""

    def test_simple_filter(self):
        """Test basic FILTER clause."""
        query = (
            select("?researcher", "?name", "?age")
            .prefix("ex", "http://example.org/")
            .where("?researcher", "a", "ex:Researcher")
            .where("?researcher", "foaf:name", "?name")
            .where("?researcher", "ex:age", "?age")
            .filter("?age > 30")
        )

        result = query.build()

        expected_lines = [
            "PREFIX ex: <http://example.org/>",
            "",
            "SELECT ?researcher ?name ?age",
            "WHERE {",
            "  ?researcher a ex:Researcher .",
            "  ?researcher foaf:name ?name .",
            "  ?researcher ex:age ?age .",
            "  FILTER (?age > 30)",
            "}"
        ]
        expected = "\n".join(expected_lines)

        assert result == expected

    def test_filter_equals(self):
        """Test FILTER with equals condition."""
        query = (
            select("?researcher", "?name")
            .prefix("ex", "http://example.org/")
            .where("?researcher", "a", "ex:Researcher")
            .where("?researcher", "foaf:name", "?name")
            .where("?researcher", "ex:department", "?dept")
            .filter_equals("?dept", "Computer Science")
        )

        result = query.build()

        expected_lines = [
            "PREFIX ex: <http://example.org/>",
            "",
            "SELECT ?researcher ?name",
            "WHERE {",
            "  ?researcher a ex:Researcher .",
            "  ?researcher foaf:name ?name .",
            "  ?researcher ex:department ?dept .",
            '  FILTER (?dept = "Computer Science")',
            "}"
        ]
        expected = "\n".join(expected_lines)

        assert result == expected

    def test_filter_regex(self):
        """Test FILTER with regex condition."""
        query = (
            select("?researcher", "?name")
            .prefix("ex", "http://example.org/")
            .where("?researcher", "a", "ex:Researcher")
            .where("?researcher", "foaf:name", "?name")
            .filter_regex("?name", "^Dr\\.", "i")
        )

        result = query.build()

        expected_lines = [
            "PREFIX ex: <http://example.org/>",
            "",
            "SELECT ?researcher ?name",
            "WHERE {",
            "  ?researcher a ex:Researcher .",
            "  ?researcher foaf:name ?name .",
            '  FILTER (REGEX(?name, "^Dr\\\\.", "i"))',
            "}"
        ]
        expected = "\n".join(expected_lines)

        assert result == expected

    def test_filter_exists(self):
        """Test FILTER EXISTS clause."""

        def add_exists_pattern(q):
            q.where("?researcher", "ex:hasPublication", "?pub")

        query = (
            select("?researcher", "?name")
            .prefix("ex", "http://example.org/")
            .where("?researcher", "a", "ex:Researcher")
            .where("?researcher", "foaf:name", "?name")
            .filter_exists(add_exists_pattern)
        )

        result = query.build()

        expected_lines = [
            "PREFIX ex: <http://example.org/>",
            "",
            "SELECT ?researcher ?name",
            "WHERE {",
            "  ?researcher a ex:Researcher .",
            "  ?researcher foaf:name ?name .",
            "  FILTER (EXISTS {",
            "    ?researcher ex:hasPublication ?pub .",
            "  })",
            "}"
        ]
        expected = "\n".join(expected_lines)

        assert result == expected

    def test_filter_not_exists(self):
        """Test FILTER NOT EXISTS clause."""

        def add_not_exists_pattern(q):
            q.where("?researcher", "ex:retiredDate", "?date")

        query = (
            select("?researcher", "?name")
            .prefix("ex", "http://example.org/")
            .where("?researcher", "a", "ex:Researcher")
            .where("?researcher", "foaf:name", "?name")
            .filter_not_exists(add_not_exists_pattern)
        )

        result = query.build()

        expected_lines = [
            "PREFIX ex: <http://example.org/>",
            "",
            "SELECT ?researcher ?name",
            "WHERE {",
            "  ?researcher a ex:Researcher .",
            "  ?researcher foaf:name ?name .",
            "  FILTER (NOT EXISTS {",
            "    ?researcher ex:retiredDate ?date .",
            "  })",
            "}"
        ]
        expected = "\n".join(expected_lines)

        assert result == expected


class TestPropertyPaths:
    """Test property path generation."""

    def test_simple_property_path(self):
        """Test basic property path."""
        query = (
            select("?researcher", "?colleague")
            .prefix("ex", "http://example.org/")
            .property_path("?researcher", "ex:collaboratesWith/ex:worksAt", "?colleague")
        )

        result = query.build()

        expected_lines = [
            "PREFIX ex: <http://example.org/>",
            "",
            "SELECT ?researcher ?colleague",
            "WHERE {",
            "  ?researcher ex:collaboratesWith/ex:worksAt ?colleague .",
            "}"
        ]
        expected = "\n".join(expected_lines)

        assert result == expected

    def test_complex_property_path(self):
        """Test complex property path with alternatives."""
        query = (
            select("?person", "?related")
            .prefix("ex", "http://example.org/")
            .property_path("?person", "(ex:supervisor|ex:supervisee)+", "?related")
            .where("?person", "a", "ex:Researcher")
        )

        result = query.build()

        expected_lines = [
            "PREFIX ex: <http://example.org/>",
            "",
            "SELECT ?person ?related",
            "WHERE {",
            "  ?person (ex:supervisor|ex:supervisee)+ ?related .",
            "  ?person a ex:Researcher .",
            "}"
        ]
        expected = "\n".join(expected_lines)

        assert result == expected


class TestQueryModifiers:
    """Test ORDER BY, LIMIT, OFFSET, GROUP BY, HAVING."""

    def test_order_by_ascending(self):
        """Test ORDER BY ascending."""
        query = (
            select("?researcher", "?name")
            .prefix("ex", "http://example.org/")
            .where("?researcher", "a", "ex:Researcher")
            .where("?researcher", "foaf:name", "?name")
            .order_by("?name")
        )

        result = query.build()

        expected_lines = [
            "PREFIX ex: <http://example.org/>",
            "",
            "SELECT ?researcher ?name",
            "WHERE {",
            "  ?researcher a ex:Researcher .",
            "  ?researcher foaf:name ?name .",
            "}",
            "ORDER BY ?name"
        ]
        expected = "\n".join(expected_lines)

        assert result == expected

    def test_order_by_descending(self):
        """Test ORDER BY descending."""
        query = (
            select("?researcher", "?name", "?age")
            .prefix("ex", "http://example.org/")
            .where("?researcher", "a", "ex:Researcher")
            .where("?researcher", "foaf:name", "?name")
            .where("?researcher", "ex:age", "?age")
            .order_by("?age", descending=True)
        )

        result = query.build()

        expected_lines = [
            "PREFIX ex: <http://example.org/>",
            "",
            "SELECT ?researcher ?name ?age",
            "WHERE {",
            "  ?researcher a ex:Researcher .",
            "  ?researcher foaf:name ?name .",
            "  ?researcher ex:age ?age .",
            "}",
            "ORDER BY DESC(?age)"
        ]
        expected = "\n".join(expected_lines)

        assert result == expected

    def test_limit_and_offset(self):
        """Test LIMIT and OFFSET."""
        query = (
            select("?researcher", "?name")
            .prefix("ex", "http://example.org/")
            .where("?researcher", "a", "ex:Researcher")
            .where("?researcher", "foaf:name", "?name")
            .order_by("?name")
            .limit(10)
            .offset(20)
        )

        result = query.build()

        expected_lines = [
            "PREFIX ex: <http://example.org/>",
            "",
            "SELECT ?researcher ?name",
            "WHERE {",
            "  ?researcher a ex:Researcher .",
            "  ?researcher foaf:name ?name .",
            "}",
            "ORDER BY ?name",
            "LIMIT 10",
            "OFFSET 20"
        ]
        expected = "\n".join(expected_lines)

        assert result == expected

    def test_group_by_and_having(self):
        """Test GROUP BY and HAVING."""
        query = (
            select("?department", "?researcher")
            .prefix("ex", "http://example.org/")
            .where("?researcher", "a", "ex:Researcher")
            .where("?researcher", "ex:department", "?department")
            .group_by("?department")
            .having("COUNT(?researcher) > 5")
        )

        result = query.build()

        expected_lines = [
            "PREFIX ex: <http://example.org/>",
            "",
            "SELECT ?department ?researcher",
            "WHERE {",
            "  ?researcher a ex:Researcher .",
            "  ?researcher ex:department ?department .",
            "}",
            "GROUP BY ?department",
            "HAVING (COUNT(?researcher) > 5)"
        ]
        expected = "\n".join(expected_lines)

        assert result == expected

    def test_complex_query_with_all_modifiers(self):
        """Test complex query with multiple modifiers."""
        query = (
            select("?department", "?researcher", "?age")
            .prefix("ex", "http://example.org/")
            .where("?researcher", "a", "ex:Researcher")
            .where("?researcher", "ex:department", "?department")
            .where("?researcher", "ex:age", "?age")
            .filter("?age >= 25")
            .group_by("?department")
            .having("COUNT(?researcher) >= 3")
            .order_by("?department")
            .limit(5)
        )

        result = query.build()

        expected_lines = [
            "PREFIX ex: <http://example.org/>",
            "",
            "SELECT ?department ?researcher ?age",
            "WHERE {",
            "  ?researcher a ex:Researcher .",
            "  ?researcher ex:department ?department .",
            "  ?researcher ex:age ?age .",
            "  FILTER (?age >= 25)",
            "}",
            "GROUP BY ?department",
            "HAVING (COUNT(?researcher) >= 3)",
            "ORDER BY ?department",
            "LIMIT 5"
        ]
        expected = "\n".join(expected_lines)

        assert result == expected
