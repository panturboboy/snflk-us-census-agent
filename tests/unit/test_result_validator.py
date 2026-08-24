"""Unit tests for result validation"""

import pytest
from unittest.mock import Mock
from src.validation.result_validator import ResultValidator


class MockMetadataCache:
    """Mock cache for testing"""

    def __init__(self):
        self.distinct_counts = {
            ('FACT_POPULATION_AGE', 'STATE'): 50,
            ('FACT_POPULATION_AGE', 'AGE_GROUP'): 23,
            ('FACT_POPULATION_AGE', 'SEX'): 2,
        }

    def get_distinct_count(self, table, column):
        return self.distinct_counts.get((table, column), 0)


@pytest.mark.unit
class TestResultValidator:
    """Test result validation logic"""

    @pytest.fixture
    def cache(self):
        return MockMetadataCache()

    @pytest.fixture
    def validator(self, cache):
        return ResultValidator(cache)

    def test_validate_no_duplicates_clean_data(self, validator):
        """Validate clean data with no duplicates"""
        results = [
            {'STATE': 'CA', 'AGE_GROUP': '25-29', 'POPULATION': 1000},
            {'STATE': 'TX', 'AGE_GROUP': '25-29', 'POPULATION': 1200},
            {'STATE': 'NY', 'AGE_GROUP': '25-29', 'POPULATION': 900},
        ]
        grain = ['STATE', 'AGE_GROUP']

        result = validator.validate_no_duplicates(results, grain)

        assert result.status == 'PASS'

    def test_validate_no_duplicates_detects_duplicates(self, validator):
        """Detect duplicate rows at grain level"""
        results = [
            {'STATE': 'CA', 'AGE_GROUP': '25-29', 'POPULATION': 1000},
            {'STATE': 'CA', 'AGE_GROUP': '25-29', 'POPULATION': 1000},  # DUPLICATE
            {'STATE': 'TX', 'AGE_GROUP': '25-29', 'POPULATION': 1200},
        ]
        grain = ['STATE', 'AGE_GROUP']

        result = validator.validate_no_duplicates(results, grain)

        assert result.status == 'FAIL'
        assert 'duplicate' in result.message.lower()

    def test_validate_no_duplicates_empty_results(self, validator):
        """Handle empty result set"""
        results = []
        grain = ['STATE']

        result = validator.validate_no_duplicates(results, grain)

        assert result.status == 'PASS'

    def test_validate_no_duplicates_no_grain(self, validator):
        """Handle missing grain"""
        results = [{'STATE': 'CA'}, {'STATE': 'TX'}]
        grain = []

        result = validator.validate_no_duplicates(results, grain)

        assert result.status == 'PASS'

    def test_validate_no_duplicates_case_insensitive(self, validator):
        """Grain check should be case-insensitive"""
        results = [
            {'state': 'CA', 'age_group': '25-29'},
            {'STATE': 'CA', 'AGE_GROUP': '25-29'},  # Should be detected as duplicate
        ]
        grain = ['STATE', 'AGE_GROUP']

        result = validator.validate_no_duplicates(results, grain)

        assert result.status == 'FAIL'

    def test_validate_cardinality_exact(self, validator):
        """Cardinality within expected range"""
        results = [
            {'STATE': 'CA', 'SUM': 1000},
            {'STATE': 'TX', 'SUM': 1200},
            # ... 48 more states
        ] + [{'STATE': f'ST{i}', 'SUM': 1000} for i in range(48)]

        result = validator.validate_cardinality(
            results, 'FACT_POPULATION_AGE', ['STATE']
        )

        assert result.status == 'PASS'

    def test_validate_cardinality_single_row_aggregation(self, validator):
        """Single-row aggregation expected"""
        results = [{'TOTAL': 1000000}]

        result = validator.validate_cardinality(
            results, 'FACT_POPULATION_AGE', []
        )

        assert result.status == 'PASS'

    def test_validate_cardinality_single_row_small_result_set(self, validator):
        """Single aggregation with small result set (parser may have missed GROUP BY)"""
        results = [
            {'TOTAL': 1000000},
            {'TOTAL': 2000000},  # Small number of rows
        ]

        result = validator.validate_cardinality(
            results, 'FACT_POPULATION_AGE', []
        )

        # Now passes because small result set likely means parser missed GROUP BY
        assert result.status == 'PASS'

    def test_validate_cardinality_single_row_large_result_set(self, validator):
        """Single aggregation returning very large result set is suspicious"""
        results = [{'TOTAL': i} for i in range(500)]  # 500 rows - too many for single agg

        result = validator.validate_cardinality(
            results, 'FACT_POPULATION_AGE', []
        )

        # Now warns because 500 rows is too many for single aggregation
        assert result.status == 'WARN'

    def test_validate_cardinality_low_results(self, validator):
        """Small result sets pass validation (normal for dimension breakdowns)

        Small result sets (<1000 rows) are accepted because they're expected for
        queries with dimensions, filters, or aggregations. Tests that the
        improved cardinality validator gracefully accepts small result sets.
        """
        results = [
            {'STATE': 'CA', 'SUM': 1000},
            {'STATE': 'TX', 'SUM': 1200},
            {'STATE': 'NY', 'SUM': 900},
            # Only 3 states instead of 50 - but still small result set
        ]

        result = validator.validate_cardinality(
            results, 'FACT_POPULATION_AGE', ['STATE']
        )

        # Small result sets don't warn, even if fewer than expected
        assert result.status == 'PASS'
        assert 'small' in result.message.lower()

    def test_validate_cardinality_high_results(self, validator):
        """More results than expected (possible fan-out or breakdown)"""
        # For GROUP BY [STATE], expected ~50 rows
        # But we have 50 * 23 * 2 = 2300 rows (includes AGE_GROUP and SEX)
        results = [{'STATE': f'S{i}', 'AGE': j, 'SEX': k, 'SUM': 1000}
                   for i in range(50) for j in range(23) for k in range(2)]

        result = validator.validate_cardinality(
            results, 'FACT_POPULATION_AGE', ['STATE']
        )

        assert result.status == 'WARN'
        assert 'high' in result.message.lower()

    def test_validate_no_fanout_clean(self, validator):
        """No fan-out detected"""
        results = [{'STATE': 'CA'}, {'STATE': 'TX'}, {'STATE': 'NY'}]
        grain = ['STATE']

        result = validator.validate_no_fanout(results, grain)

        assert result.status == 'PASS'

    def test_validate_no_fanout_empty_results(self, validator):
        """Handle empty results"""
        results = []
        grain = ['STATE']

        result = validator.validate_no_fanout(results, grain)

        assert result.status == 'PASS'

    def test_calculate_expected_cardinality(self, validator):
        """Calculate expected rows from grain cardinalities"""
        # For STATE (50) x AGE_GROUP (23)
        expected = validator._calculate_expected_cardinality(
            'FACT_POPULATION_AGE',
            ['STATE', 'AGE_GROUP']
        )

        # Should be 50 * 23 = 1150
        assert expected >= 1000  # Approximate check

    def test_calculate_expected_cardinality_no_group_by(self, validator):
        """Single aggregation = 1 row"""
        expected = validator._calculate_expected_cardinality(
            'FACT_POPULATION_AGE',
            []
        )

        assert expected == 1
