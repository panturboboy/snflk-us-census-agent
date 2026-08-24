"""Integration tests for validation pipeline"""

import pytest
from unittest.mock import Mock, patch
from src.validation import (
    QueryValidator, QueryParser, SemanticMetadataCache,
    ValidationReport
)


class MockSnowflakeClient:
    """Mock Snowflake client for integration tests"""

    @staticmethod
    def query(sql):
        """Mock Snowflake query execution"""
        if 'KEY_COLUMN_USAGE' in sql:
            # Return grain for FACT tables
            if 'FACT_POPULATION_AGE' in sql:
                return [
                    {'COLUMN_NAME': 'CENSUS_BLOCK_GROUP'},
                    {'COLUMN_NAME': 'AGE_ID'},
                    {'COLUMN_NAME': 'SEX'},
                ]
            elif 'FACT_RACE_ETHNICITY' in sql:
                return [
                    {'COLUMN_NAME': 'CENSUS_BLOCK_GROUP'},
                    {'COLUMN_NAME': 'RACE_ID'},
                ]
        elif 'ROW_COUNT' in sql:
            # Return row counts
            return [{'ROW_COUNT': 10487832}]
        elif 'COUNT(DISTINCT' in sql:
            # Return distinct counts
            if 'STATE' in sql:
                return [{'DISTINCT_COUNT': 50}]
            elif 'AGE' in sql:
                return [{'DISTINCT_COUNT': 23}]
            elif 'SEX' in sql:
                return [{'DISTINCT_COUNT': 2}]
        return []


@pytest.mark.integration
@patch('src.validation.schema_metadata.SnowflakeClient', MockSnowflakeClient)
class TestValidationPipeline:
    """Integration tests for the full validation pipeline"""

    @pytest.fixture
    def validator(self):
        """Create validator with mocked Snowflake"""
        cache = SemanticMetadataCache(refresh_minutes=60)
        return QueryValidator(cache)

    def test_validate_valid_query(self, validator):
        """Valid query should pass grain validation"""
        sql = """
        SELECT CENSUS_BLOCK_GROUP, AGE_ID, SEX, SUM(POPULATION_ESTIMATE)
        FROM CURATED.FACT_POPULATION_AGE
        GROUP BY CENSUS_BLOCK_GROUP, AGE_ID, SEX
        """

        report = validator.validate_compiled_query(sql)

        assert report.status == 'PASS'
        assert report.checks['grain']['status'] == 'PASS'

    def test_validate_invalid_grain_query(self, validator):
        """Query with missing grain columns should fail"""
        sql = """
        SELECT STATE, SUM(POPULATION_ESTIMATE)
        FROM CURATED.FACT_POPULATION_AGE
        GROUP BY STATE
        """

        report = validator.validate_compiled_query(sql)

        assert report.status == 'FAIL'
        assert report.checks['grain']['status'] == 'FAIL'

    def test_validate_single_row_aggregation(self, validator):
        """Single-row aggregation should pass"""
        sql = """
        SELECT SUM(POPULATION_ESTIMATE)
        FROM CURATED.FACT_POPULATION_AGE
        """

        report = validator.validate_compiled_query(sql)

        assert report.status == 'PASS'

    def test_validate_with_results_no_duplicates(self, validator):
        """Validate query and results with no duplicates"""
        sql = """
        SELECT CENSUS_BLOCK_GROUP, AGE_ID, SEX, SUM(POPULATION_ESTIMATE)
        FROM CURATED.FACT_POPULATION_AGE
        GROUP BY CENSUS_BLOCK_GROUP, AGE_ID, SEX
        """

        results = [
            {'CENSUS_BLOCK_GROUP': 'bg1', 'AGE_ID': 1, 'SEX': 'M', 'SUM': 100},
            {'CENSUS_BLOCK_GROUP': 'bg2', 'AGE_ID': 1, 'SEX': 'M', 'SUM': 150},
            {'CENSUS_BLOCK_GROUP': 'bg3', 'AGE_ID': 1, 'SEX': 'M', 'SUM': 120},
        ]

        report = validator.validate_compiled_query_and_results(sql, results)

        # Grain and duplicates pass; cardinality will warn because result count is low
        assert report.checks['grain']['status'] == 'PASS'
        assert report.checks['duplicates']['status'] == 'PASS'
        # Overall status may be WARN due to cardinality check on small result set
        assert report.status in ['PASS', 'WARN']

    def test_validate_with_results_duplicates_detected(self, validator):
        """Detect duplicates in results"""
        sql = """
        SELECT CENSUS_BLOCK_GROUP, AGE_ID, SEX, SUM(POPULATION_ESTIMATE)
        FROM CURATED.FACT_POPULATION_AGE
        GROUP BY CENSUS_BLOCK_GROUP, AGE_ID, SEX
        """

        results = [
            {'CENSUS_BLOCK_GROUP': 'bg1', 'AGE_ID': 1, 'SEX': 'M', 'SUM': 100},
            {'CENSUS_BLOCK_GROUP': 'bg1', 'AGE_ID': 1, 'SEX': 'M', 'SUM': 100},  # DUPLICATE
            {'CENSUS_BLOCK_GROUP': 'bg2', 'AGE_ID': 1, 'SEX': 'M', 'SUM': 150},
        ]

        report = validator.validate_compiled_query_and_results(sql, results)

        assert report.status == 'FAIL'
        assert report.checks['duplicates']['status'] == 'FAIL'

    def test_validate_with_results_cardinality_warning(self, validator):
        """Small result sets pass validation (improved cardinality logic)

        Tests that 2 results (small result set <1000 rows) pass validation even
        when the query suggests it should return thousands of rows. This is the
        correct behavior for dimension breakdowns or filtered queries.
        """
        sql = """
        SELECT CENSUS_BLOCK_GROUP, AGE_ID, SEX, SUM(POPULATION_ESTIMATE)
        FROM CURATED.FACT_POPULATION_AGE
        GROUP BY CENSUS_BLOCK_GROUP, AGE_ID, SEX
        """

        # Only 2 results instead of expected thousands
        results = [
            {'CENSUS_BLOCK_GROUP': 'bg1', 'AGE_ID': 1, 'SEX': 'M', 'SUM': 100},
            {'CENSUS_BLOCK_GROUP': 'bg2', 'AGE_ID': 1, 'SEX': 'M', 'SUM': 150},
        ]

        report = validator.validate_compiled_query_and_results(sql, results)

        # Small result sets pass validation (normal for breakdowns/filters)
        assert report.checks['cardinality']['status'] == 'PASS'

    def test_report_status_aggregation_fail_wins(self):
        """FAIL status overrides everything"""
        report = ValidationReport(status='PASS')
        report.add_check('grain', Mock(status='PASS', message='', details={}))
        report.add_check('duplicates', Mock(status='FAIL', message='', details={}))
        report.add_check('fanout', Mock(status='WARN', message='', details={}))

        report.aggregate_status()

        assert report.status == 'FAIL'

    def test_report_status_aggregation_warn_without_fail(self):
        """WARN status when no failures"""
        report = ValidationReport(status='PASS')
        report.add_check('grain', Mock(status='PASS', message='', details={}))
        report.add_check('duplicates', Mock(status='PASS', message='', details={}))
        report.add_check('fanout', Mock(status='WARN', message='', details={}))

        report.aggregate_status()

        assert report.status == 'WARN'

    def test_report_status_all_pass(self):
        """All pass = PASS"""
        report = ValidationReport(status='PASS')
        report.add_check('grain', Mock(status='PASS', message='', details={}))
        report.add_check('duplicates', Mock(status='PASS', message='', details={}))
        report.add_check('fanout', Mock(status='PASS', message='', details={}))

        report.aggregate_status()

        assert report.status == 'PASS'

    def test_validate_complex_query_with_join(self, validator):
        """Validate complex query with JOIN"""
        sql = """
        SELECT
            f.CENSUS_BLOCK_GROUP,
            f.AGE_ID,
            f.SEX,
            b.STATE_NAME_FULL,
            SUM(f.POPULATION_ESTIMATE) as total_pop
        FROM CURATED.FACT_POPULATION_AGE f
        JOIN CURATED.DIM_BLOCK_GROUP b ON f.CENSUS_BLOCK_GROUP = b.BLOCK_GROUP_ID
        WHERE f.CENSUS_YEAR = 2020
        GROUP BY f.CENSUS_BLOCK_GROUP, f.AGE_ID, f.SEX, b.STATE_NAME_FULL
        """

        report = validator.validate_compiled_query(sql)

        # Should pass because GROUP BY matches the fact table grain
        assert report.status == 'PASS'

    def test_parse_and_validate_integration(self):
        """End-to-end: parse SQL and validate"""
        sql = """
        SELECT
            CENSUS_BLOCK_GROUP,
            AGE_ID,
            SEX,
            SUM(POPULATION_ESTIMATE)
        FROM FACT_POPULATION_AGE
        GROUP BY CENSUS_BLOCK_GROUP, AGE_ID, SEX
        """

        parser = QueryParser()
        parsed = parser.parse(sql)

        assert 'FACT_POPULATION_AGE' in parsed.tables_accessed
        assert 'CENSUS_BLOCK_GROUP' in [c.upper() for c in parsed.group_by_columns]
        assert 'SUM' in parsed.aggregation_functions
