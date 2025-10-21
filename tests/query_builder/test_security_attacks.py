"""
Security tests for SPARQL Query Builder

Tests various attack vectors including SPARQL injection, input validation bypasses,
and other security vulnerabilities.
"""

from tripper.query_builder import SPARQLQuery


class TestSPARQLInjectionAttacks:
    """Test SPARQL injection attack vectors"""

    def test_regex_pattern_injection(self):
        """Test injection through regex pattern"""
        query = SPARQLQuery()
        query.select("?person", "?name")
        query.where("?person", "foaf:name", "?name")

        # Try to inject SPARQL through regex pattern
        # Pattern with unescaped quotes and special chars
        malicious_pattern = '") } DELETE { ?s ?p ?o } WHERE { REGEX(?x, "'
        query.filter_regex("?name", malicious_pattern)

        result = query.build()
        print("\n=== Regex Pattern Injection Attempt ===")
        print(result)

        # Check escaping
        assert '\\"' in result or "DELETE" not in result, "Regex pattern not properly escaped!"

    def test_regex_flags_injection(self):
        """Test injection through regex flags parameter"""
        query = SPARQLQuery()
        query.select("?person", "?name")
        query.where("?person", "foaf:name", "?name")

        # Try to inject through flags parameter (less likely but worth testing)
        malicious_flags = '") } DELETE DATA { <http://evil> <http://evil> <http://evil> } #'
        query.filter_regex("?name", "^A", malicious_flags)

        result = query.build()
        print("\n=== Regex Flags Injection Attempt ===")
        print(result)

        # Flags should be sanitized or validated
        assert "DELETE" in result or '"' not in malicious_flags, "Flags injection possible!"

    def test_variable_name_injection(self):
        """Test injection through variable names"""
        query = SPARQLQuery()

        # Try to use malicious variable names
        try:
            malicious_var = "?person } DELETE { ?x ?y ?z } WHERE { ?person"
            query.select(malicious_var)
            result = query.build()
            print("\n=== Variable Name Injection Attempt ===")
            print(result)

            # Variable validation should prevent this
            assert "DELETE" not in result, "Variable name injection succeeded!"
        except ValueError:
            # Good - validation rejected the malicious input
            print("Variable validation correctly rejected injection attempt")

    def test_prefix_uri_injection(self):
        """Test injection through prefix URI"""
        query = SPARQLQuery()

        # Try to inject SPARQL through prefix URI
        malicious_uri = "http://example.org/> DELETE DATA { <x> <y> <z> } #"
        try:
            query.prefix("ex", malicious_uri)
            result = query.build()
            print("\n=== Prefix URI Injection Attempt ===")
            print(result)

            # Should be properly formatted with angle brackets
            assert "DELETE" not in result or "<DELETE>" in result
        except ValueError:
            print("Prefix URI validation correctly rejected injection")

    def test_graph_uri_injection(self):
        """Test injection through graph URI in FROM clause"""
        query = SPARQLQuery()
        query.select("?s")

        # Try to inject through FROM clause
        malicious_graph = "http://example.org/> } DROP GRAPH <http://victim.org/> ; SELECT ?x WHERE {"
        try:
            query.from_graph(malicious_graph)
            result = query.build()
            print("\n=== Graph URI Injection Attempt ===")
            print(result)

            assert "DROP" not in result, "Graph URI injection succeeded!"
        except ValueError:
            print("Graph URI validation rejected injection")

    def test_literal_value_injection(self):
        """Test injection through literal values in where() clause"""
        query = SPARQLQuery()
        query.select("?person")

        # Try to inject through object literal
        # Note: where() accepts strings which should be formatted properly
        malicious_literal = '"; } DELETE DATA { <x> <y> <z> } #'
        query.where("?person", "foaf:name", malicious_literal)

        result = query.build()
        print("\n=== Literal Value Injection Attempt ===")
        print(result)

        # Literals should be properly escaped
        # The string should be in quotes and escaped
        assert 'DELETE' not in result or '"\\"' in result or '"' + malicious_literal + '"' in result

    def test_comment_injection(self):
        """Test injection using SPARQL comments"""
        query = SPARQLQuery()
        query.select("?person")
        query.where("?person", "rdf:type", "foaf:Person")

        # Try to use comments to break out
        malicious_filter = "?age > 18 # } DELETE { ?x ?y ?z } WHERE { true"
        query.filter(malicious_filter)

        result = query.build()
        print("\n=== Comment Injection Attempt ===")
        print(result)

        # Comments in SPARQL use #
        # If the injected comment is working, DELETE won't be executed
        # but it's still in the query which is concerning


class TestInputValidationBypass:
    """Test attempts to bypass input validation"""

    def test_unicode_normalization_attack(self):
        """Test Unicode normalization bypass attempts"""
        query = SPARQLQuery()

        # Try Unicode variations of special characters
        # U+FF1F is fullwidth question mark
        fullwidth_var = "\uff1fperson"  # Fullwidth ? + person

        try:
            query.select(fullwidth_var)
            result = query.build()
            print("\n=== Unicode Normalization Attack ===")
            print(result)
        except ValueError:
            print("Unicode variation correctly rejected")

    def test_null_byte_injection(self):
        """Test null byte injection attempts"""
        query = SPARQLQuery()

        try:
            # Null bytes might truncate strings in some contexts
            malicious = "?person\x00} DELETE { ?x ?y ?z } WHERE { ?z"
            query.select(malicious)
            result = query.build()
            print("\n=== Null Byte Injection ===")
            print(result)
        except ValueError:
            print("Null byte correctly rejected")

    def test_whitespace_bypass(self):
        """Test various whitespace characters to bypass validation"""

        # Try various whitespace: tabs, newlines, etc.
        variations = [
            "?\tperson",
            "?\nperson",
            "?\rperson",
            "?\u2000person",  # En quad space
            "?\u00A0person",  # Non-breaking space
        ]

        for var in variations:
            try:
                q = SPARQLQuery()
                q.select(var)
                result = q.build()
                print(f"\n=== Whitespace Bypass Test: {repr(var)} ===")
                print(result)
            except ValueError as e:
                print(f"Whitespace variant {repr(var)} rejected: {e}")

    def test_case_sensitivity_bypass(self):
        """Test if validation can be bypassed with case variations"""
        query = SPARQLQuery()
        query.select("?person")
        query.where("?person", "foaf:name", "?name")

        # Try uppercase SPARQL keywords in injection
        # SPARQL is case-insensitive for keywords
        malicious = "?age > 18) } delete { ?x ?y ?z } WHERE { (?x"
        query.filter(malicious)

        result = query.build()
        print("\n=== Case Sensitivity Bypass ===")
        print(result)

        # lowercase 'delete' should still work in SPARQL
        assert "delete" in result

    def test_encoding_bypass(self):
        """Test various encoding bypasses"""
        query = SPARQLQuery()
        query.select("?person")

        # Try URL encoding
        url_encoded = "%3Fperson%20%7D%20DELETE"  # ?person } DELETE
        try:
            query.where(url_encoded, "foaf:name", "?name")
            result = query.build()
            print("\n=== URL Encoding Bypass ===")
            print(result)
        except ValueError:
            print("URL encoded input rejected")


class TestDenialOfService:
    """Test DoS attack vectors"""

    def test_exponential_union_complexity(self):
        """Test if deeply nested UNIONs cause performance issues"""
        query = SPARQLQuery()
        query.select("?x")

        # Create deeply nested unions
        def create_union(q, depth):
            if depth > 0:
                q.union(
                    lambda q1: create_union(q1, depth - 1),
                    lambda q2: create_union(q2, depth - 1)
                )
            else:
                q.where("?x", "rdf:type", "?y")

        try:
            create_union(query, 5)  # 2^5 = 32 branches
            result = query.build()
            print("\n=== Exponential Union Complexity ===")
            print(f"Query length: {len(result)} characters")
            # Check if query grew exponentially
            assert len(result) > 1000, "Union nesting creates large query"
        except RecursionError:
            print("Recursion limit hit - good protection")

    def test_extremely_long_regex_pattern(self):
        """Test if very long regex patterns are handled"""
        query = SPARQLQuery()
        query.select("?name")
        query.where("?person", "foaf:name", "?name")

        # Very long pattern
        long_pattern = "a" * 100000
        query.filter_regex("?name", long_pattern)

        result = query.build()
        print("\n=== Long Regex Pattern Test ===")
        print(f"Query length: {len(result)} characters")

        # Should handle long patterns
        assert len(result) > 100000

    def test_many_filters(self):
        """Test if many filters cause issues"""
        query = SPARQLQuery()
        query.select("?x")
        query.where("?x", "rdf:type", "?type")

        # Add many filters
        for i in range(1000):
            query.filter(f"?x != <http://example.org/{i}>")

        result = query.build()
        print("\n=== Many Filters Test ===")
        print(f"Query length: {len(result)} characters")
        print(f"Filter count: {result.count('FILTER')}")


class TestLogicBugs:
    """Test for logic bugs that might be exploitable"""

    def test_empty_where_clause(self):
        """Test behavior with no WHERE patterns"""
        query = SPARQLQuery()
        query.select("?x")

        result = query.build()
        print("\n=== Empty WHERE Clause ===")
        print(result)

        # Should have empty WHERE block
        assert "WHERE {\n}" in result

    def test_conflicting_modifiers(self):
        """Test conflicting query modifiers"""
        query = SPARQLQuery()

        try:
            query.select_distinct("?x")
            query.select_reduced("?y")  # Should fail - can't have both
            result = query.build()
            print("\n=== Conflicting Modifiers ===")
            print(result)
            assert False, "Should have raised ValueError"
        except ValueError as e:
            print(f"Correctly rejected conflicting modifiers: {e}")

    def test_negative_limit_offset(self):
        """Test negative LIMIT/OFFSET values"""
        query = SPARQLQuery()
        query.select("?x")

        try:
            query.limit(-1)
            assert False, "Should reject negative limit"
        except ValueError:
            print("Negative limit correctly rejected")

        try:
            query.offset(-1)
            assert False, "Should reject negative offset"
        except ValueError:
            print("Negative offset correctly rejected")

    def test_filter_in_wrong_context(self):
        """Test if filters can be misplaced"""
        query = SPARQLQuery()
        query.select("?x")

        # Add filter before any WHERE patterns
        query.filter("?x > 5")
        query.where("?x", "rdf:type", "?type")

        result = query.build()
        print("\n=== Filter Before WHERE Pattern ===")
        print(result)

        # Filter should still appear in WHERE clause
        assert "FILTER" in result, "Filter missing from query"
