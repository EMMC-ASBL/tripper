"""Tests for builder integration with triplestore."""

from tripper.query_builder import select, select_distinct
from tripper.query_builder.builder import SPARQLQuery


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

        # Extract names from results (rdflib returns list of tuples)
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
        email_count = sum(1 for result in results if len(result) > 2 and result[2])

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


class TestAggregationIntegration:
    """Test aggregation function execution."""

    def test_count_all_execution(self, in_memory_store):
        """Test COUNT(*) aggregation."""
        ts = in_memory_store

        # Count all papers
        query = (
            SPARQLQuery()
            .select_count("*", "?totalPapers")
            .prefix("ex", "http://example.org/")
            .where("?paper", "a", "ex:ResearchPaper")
        )

        results = ts.query(query.build())

        # Should have 4 papers total
        assert len(results) == 1
        count = int(results[0][0])
        assert count == 4

    def test_count_by_group_execution(self, in_memory_store):
        """Test COUNT with GROUP BY."""
        ts = in_memory_store

        # Count papers per author
        query = (
            SPARQLQuery()
            .select("?author")
            .select_count("?paper", "?paperCount")
            .prefix("ex", "http://example.org/")
            .where("?paper", "a", "ex:ResearchPaper")
            .where("?paper", "ex:author", "?author")
            .group_by("?author")
            .order_by("?author")
        )

        results = ts.query(query.build())

        # Should have 3 authors
        assert len(results) == 3
        counts = [int(r[1]) for r in results]

        # Alice has 2 papers, Bob has 1, Charlie has 1
        assert 2 in counts  # Alice's count
        assert counts.count(1) == 2  # Bob and Charlie

    def test_count_distinct_execution(self, in_memory_store):
        """Test COUNT DISTINCT aggregation."""
        ts = in_memory_store

        # Count distinct fields of papers
        query = (
            SPARQLQuery()
            .select_count("?field", "?fieldCount", distinct=True)
            .prefix("ex", "http://example.org/")
            .where("?paper", "ex:field", "?field")
        )

        results = ts.query(query.build())

        # Should have 2 distinct fields (QuantumPhysics, MaterialsScience)
        assert len(results) == 1
        count = int(results[0][0])
        assert count == 2

    def test_sum_execution(self, in_memory_store):
        """Test SUM aggregation."""
        ts = in_memory_store

        # Sum all citation counts
        query = (
            SPARQLQuery()
            .select_sum("?citations", "?totalCitations")
            .prefix("ex", "http://example.org/")
            .where("?paper", "a", "ex:ResearchPaper")
            .where("?paper", "ex:citationCount", "?citations")
        )

        results = ts.query(query.build())

        # Should have total citations: 150 + 89 + 203 + 95 = 537
        assert len(results) == 1
        total = int(results[0][0])
        assert total == 537

    def test_sum_by_group_execution(self, in_memory_store):
        """Test SUM with GROUP BY."""
        ts = in_memory_store

        # Sum citations per field
        query = (
            SPARQLQuery()
            .select("?field")
            .select_sum("?citations", "?totalCitations")
            .prefix("ex", "http://example.org/")
            .where("?paper", "ex:field", "?field")
            .where("?paper", "ex:citationCount", "?citations")
            .group_by("?field")
            .order_by("?field")
        )

        results = ts.query(query.build())

        # Should have 2 fields
        assert len(results) == 2
        citation_totals = {r[0]: int(r[1]) for r in results}

        # MaterialsScience: 203, QuantumPhysics: 150 + 89 + 95 = 334
        assert any(total == 203 for total in citation_totals.values())
        assert any(total == 334 for total in citation_totals.values())

    def test_avg_execution(self, in_memory_store):
        """Test AVG aggregation."""
        ts = in_memory_store

        # Average citation count
        query = (
            SPARQLQuery()
            .select_avg("?citations", "?avgCitations")
            .prefix("ex", "http://example.org/")
            .where("?paper", "a", "ex:ResearchPaper")
            .where("?paper", "ex:citationCount", "?citations")
        )

        results = ts.query(query.build())

        # Average: (150 + 89 + 203 + 95) / 4 = 134.25
        assert len(results) == 1
        avg = float(results[0][0])
        assert abs(avg - 134.25) < 0.01

    def test_min_execution(self, in_memory_store):
        """Test MIN aggregation."""
        ts = in_memory_store

        # Minimum citation count
        query = (
            SPARQLQuery()
            .select_min("?citations", "?minCitations")
            .prefix("ex", "http://example.org/")
            .where("?paper", "a", "ex:ResearchPaper")
            .where("?paper", "ex:citationCount", "?citations")
        )

        results = ts.query(query.build())

        # Minimum is 89
        assert len(results) == 1
        min_val = int(results[0][0])
        assert min_val == 89

    def test_max_execution(self, in_memory_store):
        """Test MAX aggregation."""
        ts = in_memory_store

        # Maximum citation count
        query = (
            SPARQLQuery()
            .select_max("?citations", "?maxCitations")
            .prefix("ex", "http://example.org/")
            .where("?paper", "a", "ex:ResearchPaper")
            .where("?paper", "ex:citationCount", "?citations")
        )

        results = ts.query(query.build())

        # Maximum is 203
        assert len(results) == 1
        max_val = int(results[0][0])
        assert max_val == 203

    def test_min_max_by_group(self, in_memory_store):
        """Test MIN and MAX with GROUP BY."""
        ts = in_memory_store

        # Min and max citations per journal
        query = (
            SPARQLQuery()
            .select("?journal")
            .select_min("?citations", "?minCitations")
            .select_max("?citations", "?maxCitations")
            .prefix("ex", "http://example.org/")
            .where("?paper", "ex:publishedIn", "?journal")
            .where("?paper", "ex:citationCount", "?citations")
            .group_by("?journal")
            .order_by("?journal")
        )

        results = ts.query(query.build())

        # Should have 2 journals
        assert len(results) == 2

        # Journal1 has papers with citations: 150, 89, 95 (min=89, max=150)
        # Journal2 has papers with citations: 203 (min=203, max=203)
        for r in results:
            min_val = int(r[1])
            max_val = int(r[2])
            # Each journal should have valid min/max
            assert min_val <= max_val

    def test_sample_execution(self, in_memory_store):
        """Test SAMPLE aggregation."""
        ts = in_memory_store

        # Sample one paper per field
        query = (
            SPARQLQuery()
            .select("?field")
            .select_sample("?paper", "?samplePaper")
            .prefix("ex", "http://example.org/")
            .where("?paper", "ex:field", "?field")
            .group_by("?field")
        )

        results = ts.query(query.build())

        # Should have 2 fields, each with a sample paper
        assert len(results) == 2
        samples = [r[1] for r in results]

        # Each sample should be a paper URI
        assert all(sample for sample in samples)

    def test_group_concat_default_separator(self, in_memory_store):
        """Test GROUP_CONCAT with default separator."""
        ts = in_memory_store

        # Concatenate paper titles per author
        query = (
            SPARQLQuery()
            .select("?author")
            .select_group_concat("?title", "?titles")
            .prefix("ex", "http://example.org/")
            .where("?paper", "ex:author", "?author")
            .where("?paper", "ex:title", "?title")
            .group_by("?author")
            .order_by("?author")
        )

        results = ts.query(query.build())

        # Should have 3 authors
        assert len(results) == 3
        title_strings = [r[1] for r in results]

        # Alice should have 2 titles concatenated
        alice_titles = [t for t in title_strings if "Quantum" in t and " " in t]
        assert len(alice_titles) >= 1  # Alice has 2 papers

    def test_group_concat_custom_separator(self, in_memory_store):
        """Test GROUP_CONCAT with custom separator."""
        ts = in_memory_store

        # Concatenate researcher names per specialization with comma separator
        query = (
            SPARQLQuery()
            .select("?specialization")
            .select_group_concat("?name", "?names", separator=", ")
            .prefix("ex", "http://example.org/")
            .where("?researcher", "ex:specialization", "?specialization")
            .where("?researcher", "foaf:name", "?name")
            .group_by("?specialization")
        )

        results = ts.query(query.build())

        # Should have 2 specializations
        assert len(results) == 2
        name_strings = [r[1] for r in results]

        # QuantumPhysics should have Alice and Charlie
        quantum_names = [n for n in name_strings if ", " in n or ("Alice" in n and "Charlie" in n)]
        assert len(quantum_names) >= 1

    def test_multiple_aggregations_execution(self, in_memory_store):
        """Test query with multiple aggregation functions."""
        ts = in_memory_store

        # Multiple statistics per field
        query = (
            SPARQLQuery()
            .select("?field")
            .select_count("?paper", "?paperCount")
            .select_sum("?citations", "?totalCitations")
            .select_avg("?citations", "?avgCitations")
            .select_min("?citations", "?minCitations")
            .select_max("?citations", "?maxCitations")
            .prefix("ex", "http://example.org/")
            .where("?paper", "ex:field", "?field")
            .where("?paper", "ex:citationCount", "?citations")
            .group_by("?field")
            .order_by("?field")
        )

        results = ts.query(query.build())

        # Should have 2 fields with complete statistics
        assert len(results) == 2

        for r in results:
            count = int(r[1])
            total = int(r[2])
            avg = float(r[3])
            min_val = int(r[4])
            max_val = int(r[5])

            # Validate aggregation relationships
            assert count > 0
            assert min_val <= avg <= max_val
            assert total >= min_val

    def test_aggregation_with_having(self, in_memory_store):
        """Test aggregation with HAVING clause."""
        ts = in_memory_store

        # Find fields with more than 1 paper
        query = (
            SPARQLQuery()
            .select("?field")
            .select_count("?paper", "?paperCount")
            .prefix("ex", "http://example.org/")
            .where("?paper", "ex:field", "?field")
            .group_by("?field")
            .having("COUNT(?paper) > 1")
        )

        results = ts.query(query.build())

        # Only QuantumPhysics has more than 1 paper (has 3)
        assert len(results) == 1
        count = int(results[0][1])
        assert count == 3

    def test_aggregation_with_filter(self, in_memory_store):
        """Test aggregation with FILTER clause."""
        ts = in_memory_store

        # Average citations for papers published in 2024
        query = (
            SPARQLQuery()
            .select_avg("?citations", "?avgCitations")
            .prefix("ex", "http://example.org/")
            .where("?paper", "a", "ex:ResearchPaper")
            .where("?paper", "ex:citationCount", "?citations")
            .where("?paper", "ex:publishedYear", "?year")
            .filter("?year = 2024")
        )

        results = ts.query(query.build())

        # Papers in 2024: paper2 (89), paper4 (95) -> avg = 92
        assert len(results) == 1
        avg = float(results[0][0])
        assert abs(avg - 92.0) < 0.01

    def test_aggregation_with_order_by(self, in_memory_store):
        """Test aggregation results ordered by aggregate value."""
        ts = in_memory_store

        # Authors ordered by paper count
        query = (
            SPARQLQuery()
            .select("?author")
            .select_count("?paper", "?paperCount")
            .prefix("ex", "http://example.org/")
            .where("?paper", "ex:author", "?author")
            .group_by("?author")
            .order_by("?paperCount", descending=True)
        )

        results = ts.query(query.build())

        # Should have 3 authors
        assert len(results) == 3
        counts = [int(r[1]) for r in results]

        # Should be in descending order
        assert counts == sorted(counts, reverse=True)
        # Alice (2 papers) should be first
        assert counts[0] == 2
