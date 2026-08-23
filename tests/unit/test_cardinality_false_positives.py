"""Test: Fix for cardinality validator false positives

Why this test exists:
- Cardinality validator was showing warnings for correct queries
- "Sex breakdown" returned 2 rows but warned "expected ~1, got 2"
- "County breakdown" returned 58 rows but warned "expected ~1, got 58"
- Root cause: GROUP BY columns exist but distinct count lookup fails
  Result: expected = 1, triggering false positive warnings
- Fix: Skip cardinality warnings when expected = 1 with GROUP BY
  OR result is small (<1000 rows, normal for dimension breakdowns)
"""

import pytest
from unittest.mock import Mock, patch
from src.validation.result_validator import ResultValidator


class TestCardinalityFalsePositives:
    """Verify cardinality validator doesn't warn on correct breakdown queries"""

    def test_sex_breakdown_no_warning(self):
        """Test: Sex breakdown (2 rows) should not warn

        Why: Querying by sex returns 2 rows (MALE, FEMALE)
        Expected vs Actual:
        - Parser extracts: GROUP BY SEX
        - Expected from metadata: ~2 distinct values
        - Actual result: 2 rows
        Result: ✅ Should PASS, not warn
        """
        # Create mock cache that fails to get distinct counts
        mock_cache = Mock()
        mock_cache.get_distinct_count.return_value = None  # Metadata lookup fails
        mock_cache.cache = {}

        validator = ResultValidator(mock_cache)

        # Simulate sex breakdown results (2 rows)
        results = [
            ('FL', 'MALE', 5000000),
            ('FL', 'FEMALE', 5100000),
        ]

        result = validator.validate_cardinality(
            results,
            table_name='FACT_POPULATION_AGE',
            group_by_columns=['SEX']
        )

        # Should NOT warn for small result set with GROUP BY
        assert result.status != 'FAIL', "Sex breakdown should not fail"
        assert 'High cardinality' not in result.message, \
            f"False positive: {result.message}"

    def test_county_breakdown_no_warning(self):
        """Test: County breakdown (58 rows) should not warn

        Why: Querying by county returns ~58 rows (one per CA county)
        Expected vs Actual:
        - Parser extracts: GROUP BY COUNTY
        - Expected from metadata: ~58 distinct counties
        - Actual result: 58 rows
        - Metadata might be unavailable/wrong expected = 1
        Result: ✅ Should PASS, not warn (result < 1000 rows)
        """
        mock_cache = Mock()
        mock_cache.get_distinct_count.return_value = 1  # Fails, returns 1
        mock_cache.cache = {}

        validator = ResultValidator(mock_cache)

        # Simulate county breakdown results (58 rows for CA)
        results = [(f'COUNTY_{i}', 1000000) for i in range(58)]

        result = validator.validate_cardinality(
            results,
            table_name='FACT_POPULATION_AGE',
            group_by_columns=['COUNTY']
        )

        # Should NOT warn for small result set
        assert result.status != 'FAIL', "County breakdown should not fail"
        assert 'High cardinality' not in result.message, \
            f"False positive: {result.message}"

    def test_expected_one_with_groupby_skips_validation(self):
        """Test: If expected=1 but GROUP BY exists, skip validation

        Why: When expected=1 despite GROUP BY, it means metadata lookup failed
        We should not warn - it's a sign our metadata is stale/unavailable
        """
        mock_cache = Mock()
        # Simulate failed metadata lookup (returns 0 or None)
        mock_cache.get_distinct_count.return_value = 0
        mock_cache.cache = {}

        validator = ResultValidator(mock_cache)

        # Any breakdown with GROUP BY should pass if result is reasonable
        results = [f'ROW_{i}' for i in range(100)]

        result = validator.validate_cardinality(
            results,
            table_name='FACT_POPULATION_AGE',
            group_by_columns=['SOME_DIMENSION']
        )

        # Should pass with message about skipping validation
        assert result.status == 'PASS', \
            f"Should skip validation when expected=1 with GROUP BY, got: {result.message}"

    def test_small_result_sets_dont_warn(self):
        """Test: Result sets < 1000 rows should not trigger cardinality warning

        Why: Dimension breakdowns are typically small:
        - Sex: 2-3 rows
        - County: 50-100 rows
        - Age groups: 20-30 rows
        - Etc.
        These are all correct queries that shouldn't warn.
        """
        mock_cache = Mock()
        mock_cache.get_distinct_count.return_value = 1  # Metadata fails
        mock_cache.cache = {}

        validator = ResultValidator(mock_cache)

        # Test various small result sets
        test_cases = [
            (2, 'SEX breakdown'),
            (58, 'COUNTY breakdown'),
            (25, 'AGE_GROUP breakdown'),
            (999, 'Large dimension breakdown'),
        ]

        for row_count, description in test_cases:
            results = [f'ROW_{i}' for i in range(row_count)]

            result = validator.validate_cardinality(
                results,
                table_name='FACT_POPULATION_AGE',
                group_by_columns=['SOME_DIM']
            )

            assert result.status == 'PASS', \
                f"{description}: {row_count} rows should not warn. Got: {result.message}"
            # Should not show warnings (High/Low cardinality)
            assert 'High cardinality' not in result.message and 'Low cardinality' not in result.message, \
                f"{description}: Should not warn about cardinality issues"

    def test_very_large_result_still_warns(self):
        """Test: Very large results (>100K) should still warn appropriately

        Why: Even if metadata fails, 100K+ rows for a single breakdown is suspect
        Should warn about possible fan-out or join issues
        """
        mock_cache = Mock()
        mock_cache.get_distinct_count.return_value = 50  # Reasonable estimate
        mock_cache.cache = {}

        validator = ResultValidator(mock_cache)

        # Simulate suspiciously large result
        results = [f'ROW_{i}' for i in range(100000)]

        result = validator.validate_cardinality(
            results,
            table_name='FACT_POPULATION_AGE',
            group_by_columns=['SEX']
        )

        # Should warn about unusually high cardinality
        assert 'cardinality' in result.message.lower() or result.status == 'WARN', \
            f"Should warn about 100K rows for sex breakdown. Got: {result.message}"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
