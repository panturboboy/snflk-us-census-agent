"""Unit tests for grain validation"""

import pytest
from unittest.mock import Mock, MagicMock
from src.validation.grain_validator import GrainValidator, ValidationResult
from src.validation.query_parser import QueryStructure


class MockMetadataCache:
    """Mock cache for testing"""

    def __init__(self):
        self.grain_map = {
            'FACT_POPULATION_AGE': ['CENSUS_BLOCK_GROUP', 'AGE_ID', 'SEX'],
            'FACT_RACE_ETHNICITY': ['CENSUS_BLOCK_GROUP', 'RACE_ID'],
            'FACT_HOUSEHOLD_COMPOSITION': ['CENSUS_BLOCK_GROUP', 'HOUSEHOLD_TYPE_ID']
        }

    def get_grain(self, table_name):
        return self.grain_map.get(table_name, [])


@pytest.mark.unit
class TestGrainValidator:
    """Test grain validation logic"""

    @pytest.fixture
    def cache(self):
        return MockMetadataCache()

    @pytest.fixture
    def validator(self, cache):
        return GrainValidator(cache)

    def test_grain_exact_match(self, validator):
        """Query GROUP BY exactly matches fact table grain"""
        parsed = QueryStructure(
            tables_accessed=['FACT_POPULATION_AGE'],
            columns_selected=['CENSUS_BLOCK_GROUP', 'AGE_ID', 'SUM(POPULATION)'],
            group_by_columns=['CENSUS_BLOCK_GROUP', 'AGE_ID', 'SEX'],
            aggregation_functions=['SUM']
        )

        result = validator.validate(parsed)

        assert result.status == 'PASS'

    def test_grain_roll_up_valid(self, validator):
        """Query GROUP BY is subset of grain (valid roll-up)"""
        parsed = QueryStructure(
            tables_accessed=['FACT_POPULATION_AGE'],
            columns_selected=['STATE', 'SUM(POPULATION)'],
            group_by_columns=['STATE'],
            aggregation_functions=['SUM']
        )

        result = validator.validate(parsed)

        # This should FAIL because STATE is not in the grain
        # Grain = [BLOCK_GROUP, AGE_ID, SEX]
        # GROUP BY = [STATE]
        # Missing: BLOCK_GROUP (critical dimension)
        assert result.status == 'FAIL'

    def test_grain_no_group_by_aggregation(self, validator):
        """Single-row aggregation with no GROUP BY"""
        parsed = QueryStructure(
            tables_accessed=['FACT_POPULATION_AGE'],
            columns_selected=['SUM(POPULATION)'],
            group_by_columns=[],
            aggregation_functions=['SUM']
        )

        result = validator.validate(parsed)

        assert result.status == 'PASS'

    def test_grain_mismatch_missing_columns(self, validator):
        """Query GROUP BY is missing grain columns"""
        parsed = QueryStructure(
            tables_accessed=['FACT_POPULATION_AGE'],
            columns_selected=['CENSUS_BLOCK_GROUP', 'AGE_ID', 'SUM(POPULATION)'],
            group_by_columns=['CENSUS_BLOCK_GROUP', 'AGE_ID'],  # Missing SEX!
            aggregation_functions=['SUM']
        )

        result = validator.validate(parsed)

        assert result.status == 'FAIL'
        assert 'mismatch' in result.message.lower()

    def test_grain_case_insensitive(self, validator):
        """Column names should be case-insensitive"""
        parsed = QueryStructure(
            tables_accessed=['FACT_POPULATION_AGE'],
            columns_selected=['census_block_group', 'age_id', 'sum(population)'],
            group_by_columns=['census_block_group', 'age_id', 'sex'],
            aggregation_functions=['SUM']
        )

        result = validator.validate(parsed)

        assert result.status == 'PASS'

    def test_grain_dimension_table_skipped(self, validator):
        """Dimension tables should be skipped (no grain check)"""
        parsed = QueryStructure(
            tables_accessed=['DIM_BLOCK_GROUP'],
            columns_selected=['BLOCK_GROUP', 'STATE'],
            group_by_columns=['BLOCK_GROUP'],
            aggregation_functions=[]
        )

        result = validator.validate(parsed)

        # Should pass because DIM_ tables are skipped
        assert result.status == 'PASS'

    def test_grain_empty_table_list(self, validator):
        """Handle empty table list"""
        parsed = QueryStructure(
            tables_accessed=[],
            columns_selected=['COLUMN'],
            group_by_columns=['COLUMN'],
            aggregation_functions=[]
        )

        result = validator.validate(parsed)

        assert result.status == 'PASS'

    def test_grain_multiple_tables_first_fact(self, validator):
        """Validate grain when multiple tables, first one is fact"""
        parsed = QueryStructure(
            tables_accessed=['FACT_POPULATION_AGE', 'DIM_BLOCK_GROUP'],
            columns_selected=['CENSUS_BLOCK_GROUP', 'AGE_ID', 'SUM(POPULATION)'],
            group_by_columns=['CENSUS_BLOCK_GROUP', 'AGE_ID', 'SEX'],
            aggregation_functions=['SUM']
        )

        result = validator.validate(parsed)

        assert result.status == 'PASS'

    def test_grain_validation_unknown_table(self, validator, cache):
        """Handle unknown table gracefully"""
        # Mock get_grain to return empty list
        cache.grain_map['UNKNOWN_TABLE'] = []

        parsed = QueryStructure(
            tables_accessed=['UNKNOWN_TABLE'],
            columns_selected=['COL1'],
            group_by_columns=['COL1'],
            aggregation_functions=[]
        )

        result = validator.validate(parsed)

        # Should pass (unknown tables are skipped)
        assert result.status == 'PASS'

    def test_grain_matches_logic_exact(self, validator):
        """Test _grain_matches logic: exact match"""
        grain = ['A', 'B', 'C']
        group_by = ['A', 'B', 'C']

        assert validator._grain_matches(grain, group_by) is True

    def test_grain_matches_logic_no_group_by(self, validator):
        """Test _grain_matches logic: no GROUP BY (single aggregation)"""
        grain = ['A', 'B', 'C']
        group_by = []

        assert validator._grain_matches(grain, group_by) is True

    def test_grain_matches_logic_subset_invalid(self, validator):
        """Test _grain_matches logic: subset of grain (invalid)"""
        grain = ['A', 'B', 'C']
        group_by = ['A', 'B']  # Missing C

        assert validator._grain_matches(grain, group_by) is False

    def test_grain_matches_logic_superset_valid(self, validator):
        """Test _grain_matches logic: superset of grain (valid roll-up)"""
        grain = ['A', 'B']
        group_by = ['A', 'B', 'C']  # Has grain + C

        assert validator._grain_matches(grain, group_by) is True
