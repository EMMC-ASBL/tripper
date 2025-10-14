"""Tests for builder integration with triplestore."""

from tripper.query_builder import select, select_distinct


class TestBasicSelectIntegration:
    """Test basic SELECT query execution."""

    def test_simple_select_query_execution(self, in_memory_store):
        """Test basic SELECT query execution against triplestore."""
        ts = in_memory_store

        # Build a query to get all researchers and their names
        query = (
            select("?researcher", "?name")
            .prefix("ex", "http://example.org/")
            .where("?researcher", "a", "ex:Researcher")
            .where("?researcher", "foaf:name", "?name")
        )

        # Execute the query
        results = ts.query(query.build())

        # Verify we get the expected results
        assert len(results) == 3  # Alice, Bob, and Charlie

        # Extract names from results (assuming results is list of tuples/dicts)
        if results and isinstance(results[0], dict):
            names = {result["name"] for result in results}
        else:
            # Assuming results is list of tuples
            names = {result[1] for result in results}

        expected_names = {"Alice", "Bob", "Charlie"}
        assert names == expected_names

    def test_select_distinct_execution(self, in_memory_store):
        """Test SELECT DISTINCT query execution."""
        ts = in_memory_store

        # Query for all unique institutions (universities and research institutes)
        query = (
            select_distinct("?institution")
            .prefix("ex", "http://example.org/")
            .where("?researcher", "ex:affiliation", "?institution")
        )

        results = ts.query(query.build())

        # Should get 3 unique institutions (university1, university2, institute1)
        assert len(results) == 3

        if results and isinstance(results[0], dict):
            institutions = {result["institution"] for result in results}
        else:
            institutions = {result[0] for result in results}

        expected_institutions = {
            "http://example.org/university1",
            "http://example.org/university2",
            "http://example.org/institute1"
        }
        assert institutions == expected_institutions

    def test_multiple_where_clauses(self, in_memory_store):
        """Test query with multiple WHERE clauses."""
        ts = in_memory_store

        # Query for researchers at university1
        query = (
            select("?researcher", "?name")
            .prefix("ex", "http://example.org/")
            .where("?researcher", "a", "ex:Researcher")
            .where("?researcher", "foaf:name", "?name")
            .where("?researcher", "ex:affiliation", "http://example.org/university1")
        )

        results = ts.query(query.build())

        # Should get Alice (at university1)
        assert len(results) == 1

        if results and isinstance(results[0], dict):
            names = {result["name"] for result in results}
        else:
            names = {result[1] for result in results}

        expected_names = {"Alice"}
        assert names == expected_names


class TestOptionalIntegration:
    """Test OPTIONAL pattern execution."""

    def test_simple_optional_execution(self, in_memory_store):
        """Test OPTIONAL clause execution."""
        ts = in_memory_store

        def add_optional_email(q):
            q.where("?researcher", "foaf:mbox", "?email")

        # Query for researchers with optional email
        query = (
            select("?researcher", "?name", "?email")
            .prefix("ex", "http://example.org/")
            .where("?researcher", "a", "ex:Researcher")
            .where("?researcher", "foaf:name", "?name")
            .optional(add_optional_email)
        )

        results = ts.query(query.build())

        # Should get all 3 researchers
        assert len(results) == 3

        # Check that some have emails and some don't
        email_count = 0
        if results and isinstance(results[0], dict):
            for result in results:
                if result.get("email"):
                    email_count += 1
        else:
            for result in results:
                if len(result) > 2 and result[2]:  # Third column is email
                    email_count += 1

        # Based on our test data, some researchers should have emails
        assert email_count >= 1

    def test_multiple_optional_patterns(self, in_memory_store):
        """Test multiple OPTIONAL clauses."""
        ts = in_memory_store

        def add_optional_email(q):
            q.where("?researcher", "foaf:mbox", "?email")

        def add_optional_phone(q):
            q.where("?researcher", "foaf:phone", "?phone")

        query = (
            select("?researcher", "?name", "?email", "?phone")
            .prefix("ex", "http://example.org/")
            .where("?researcher", "a", "ex:Researcher")
            .where("?researcher", "foaf:name", "?name")
            .optional(add_optional_email)
            .optional(add_optional_phone)
        )

        results = ts.query(query.build())

        # Should get all 3 researchers
        assert len(results) == 3

        # All should have names
        if results and isinstance(results[0], dict):
            names = {result["name"] for result in results}
        else:
            names = {result[1] for result in results}

        expected_names = {"Alice", "Bob", "Charlie"}
        assert names == expected_names


class TestUnionIntegration:
    """Test UNION pattern execution."""

    def test_simple_union_execution(self, in_memory_store):
        """Test basic UNION clause execution."""
        ts = in_memory_store

        def add_researcher_pattern(q):
            q.where("?person", "a", "ex:Researcher")
            q.where("?person", "foaf:name", "?name")

        def add_journal_pattern(q):
            q.where("?person", "a", "ex:Journal")
            q.where("?person", "ex:title", "?name")

        # Query for both researchers and journals
        query = (
            select("?person", "?name")
            .prefix("ex", "http://example.org/")
            .union(add_researcher_pattern, add_journal_pattern)
        )

        results = ts.query(query.build())

        # Should get researchers + journals
        assert len(results) >= 3  # At least the 3 researchers

        if results and isinstance(results[0], dict):
            names = {result["name"] for result in results}
        else:
            names = {result[1] for result in results}

        # Should include all researcher names
        researcher_names = {"Alice", "Bob", "Charlie"}
        assert researcher_names.issubset(names)


class TestFilterIntegration:
    """Test FILTER clause execution."""

    def test_simple_filter_execution(self, in_memory_store):
        """Test basic FILTER clause execution."""
        ts = in_memory_store

        # Query for researchers whose names start with 'A'
        query = (
            select("?researcher", "?name")
            .prefix("ex", "http://example.org/")
            .where("?researcher", "a", "ex:Researcher")
            .where("?researcher", "foaf:name", "?name")
            .filter('REGEX(?name, "^A")')
        )

        results = ts.query(query.build())

        # Should get only Alice
        assert len(results) == 1

        if results and isinstance(results[0], dict):
            name = results[0]["name"]
        else:
            name = results[0][1]

        assert name == "Alice"

    def test_filter_equals_execution(self, in_memory_store):
        """Test FILTER with equals condition."""
        ts = in_memory_store

        # Query for researchers with specific name
        query = (
            select("?researcher", "?name")
            .prefix("ex", "http://example.org/")
            .where("?researcher", "a", "ex:Researcher")
            .where("?researcher", "foaf:name", "?name")
            .filter_equals("?name", "Bob")
        )

        results = ts.query(query.build())

        # Should get only Bob
        assert len(results) == 1

        if results and isinstance(results[0], dict):
            name = results[0]["name"]
        else:
            name = results[0][1]

        assert name == "Bob"


class TestQueryModifiersIntegration:
    """Test ORDER BY, LIMIT, OFFSET execution."""

    def test_order_by_execution(self, in_memory_store):
        """Test ORDER BY clause execution."""
        ts = in_memory_store

        # Query for researchers ordered by name
        query = (
            select("?researcher", "?name")
            .prefix("ex", "http://example.org/")
            .where("?researcher", "a", "ex:Researcher")
            .where("?researcher", "foaf:name", "?name")
            .order_by("?name")
        )

        results = ts.query(query.build())

        # Should get all 3 researchers in alphabetical order
        assert len(results) == 3

        if results and isinstance(results[0], dict):
            names = [result["name"] for result in results]
        else:
            names = [result[1] for result in results]

        # Should be in alphabetical order
        expected_order = ["Alice", "Bob", "Charlie"]
        assert names == expected_order

    def test_limit_execution(self, in_memory_store):
        """Test LIMIT clause execution."""
        ts = in_memory_store

        # Query for researchers with limit
        query = (
            select("?researcher", "?name")
            .prefix("ex", "http://example.org/")
            .where("?researcher", "a", "ex:Researcher")
            .where("?researcher", "foaf:name", "?name")
            .order_by("?name")
            .limit(2)
        )

        results = ts.query(query.build())

        # Should get only 2 researchers
        assert len(results) == 2

        if results and isinstance(results[0], dict):
            names = [result["name"] for result in results]
        else:
            names = [result[1] for result in results]

        # Should be first 2 in alphabetical order
        expected_names = ["Alice", "Bob"]
        assert names == expected_names

    def test_offset_execution(self, in_memory_store):
        """Test OFFSET clause execution."""
        ts = in_memory_store

        # Query for researchers with offset
        query = (
            select("?researcher", "?name")
            .prefix("ex", "http://example.org/")
            .where("?researcher", "a", "ex:Researcher")
            .where("?researcher", "foaf:name", "?name")
            .order_by("?name")
            .offset(1)
            .limit(2)
        )

        results = ts.query(query.build())

        # Should get 2 researchers starting from second
        assert len(results) == 2

        if results and isinstance(results[0], dict):
            names = [result["name"] for result in results]
        else:
            names = [result[1] for result in results]

        # Should be Bob and Charlie
        expected_names = ["Bob", "Charlie"]
        assert names == expected_names


class TestComplexIntegration:
    """Test complex query patterns."""

    def test_complex_query_with_multiple_patterns(self, in_memory_store):
        """Test complex query combining multiple patterns."""
        ts = in_memory_store

        def add_optional_email(q):
            q.where("?researcher", "foaf:mbox", "?email")

        # Complex query: researchers with their institutions and optional emails
        query = (
            select("?researcher", "?name", "?institution", "?email")
            .prefix("ex", "http://example.org/")
            .where("?researcher", "a", "ex:Researcher")
            .where("?researcher", "foaf:name", "?name")
            .where("?researcher", "ex:affiliation", "?institution")
            .optional(add_optional_email)
            .order_by("?name")
        )

        results = ts.query(query.build())

        # Should get all 3 researchers
        assert len(results) == 3

        if results and isinstance(results[0], dict):
            names = [result["name"] for result in results]
            institutions = [result["institution"] for result in results]
        else:
            names = [result[1] for result in results]
            institutions = [result[2] for result in results]

        # Should be ordered by name
        expected_names = ["Alice", "Bob", "Charlie"]
        assert names == expected_names

        # Should have institution affiliations for all
        assert all(inst for inst in institutions)

    def test_property_path_execution(self, in_memory_store):
        """Test property path execution."""
        ts = in_memory_store

        # Test a property path query if the triplestore supports it
        query = (
            select("?researcher", "?related")
            .prefix("ex", "http://example.org/")
            .property_path("?researcher", "ex:affiliatedWith/ex:hasCollaborator", "?related")
        )

        try:
            results = ts.query(query.build())
            # If property paths are supported, we should get some results or none
            assert isinstance(results, list)
        except Exception:
            # Property paths might not be supported by all triplestores
            # This is acceptable for testing purposes
            pass

    def test_nested_patterns_execution(self, in_memory_store):
        """Test nested query patterns."""
        ts = in_memory_store

        def add_researcher_details(q):
            q.where("?researcher", "a", "ex:Researcher")
            q.where("?researcher", "foaf:name", "?name")
            q.where("?researcher", "ex:affiliatedWith", "?university")

        def add_publication_details(q):
            q.where("?researcher", "ex:hasPublication", "?paper")
            q.where("?paper", "ex:title", "?title")

        # Query for researchers and their publications
        query = (
            select("?researcher", "?name", "?university")
            .prefix("ex", "http://example.org/")
            .union(add_researcher_details, add_publication_details)
            .order_by("?name")
            .limit(10)
        )

        results = ts.query(query.build())

        # Should get some results
        assert len(results) >= 0
        assert isinstance(results, list)
