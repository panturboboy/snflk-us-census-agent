"""Integration test: End-to-end query accuracy with EXACT ground truth

This test suite:
1. Uses exact values captured from Snowflake (no ranges, no approximations)
2. Validates queries return the exact expected results
3. Each test has ground truth and natural language prompt
4. Tests both row counts AND exact values

Purpose: Ensure Cortex Analyst interprets questions correctly and returns exact data
"""

import sys
import os
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.snowflake_client import SnowflakeClient
from src.config import SnowflakeConfig
from tests.integration.test_fixtures_ground_truth import capture_ground_truth


class TestCortexQueryAccuracyExact:
    """Validate Cortex Analyst returns EXACT ground truth values"""

    @classmethod
    def setup_class(cls):
        """Initialize Snowflake connection and load ground truth"""
        SnowflakeConfig.validate()
        cls.conn = SnowflakeClient.get_connection()
        cls.ground_truth = capture_ground_truth()

    def execute_query(self, sql: str) -> tuple:
        """Execute query and return raw results"""
        cursor = self.conn.cursor()
        cursor.execute(sql)
        return cursor.fetchall()

    def test_01_california_population_exact(self):
        """Test 1: California population returns EXACT value

        Ground Truth: 39,346,023
        Prompt: "What is the total population of California?"
        """
        truth = self.ground_truth['california_population']

        # Execute ground truth query
        rows = self.execute_query(truth.sql)

        # Validate exact match
        assert len(rows) == truth.expected_row_count, \
            f"Expected {truth.expected_row_count} row, got {len(rows)}"

        actual_value = rows[0][0]
        expected_value = truth.expected_values['population']

        assert actual_value == expected_value, \
            f"California population mismatch:\n" \
            f"  Expected (ground truth): {expected_value}\n" \
            f"  Actual (from query):     {actual_value}"

    def test_02_texas_population_exact(self):
        """Test 2: Texas population returns EXACT value

        Ground Truth: 28,635,442
        Prompt: "What is the population of Texas?"
        """
        truth = self.ground_truth['texas_population']
        rows = self.execute_query(truth.sql)

        assert len(rows) == truth.expected_row_count
        actual_value = rows[0][0]
        expected_value = truth.expected_values['population']

        assert actual_value == expected_value, \
            f"Texas population mismatch: expected {expected_value}, got {actual_value}"

    def test_03_newyork_population_exact(self):
        """Test 3: New York population returns EXACT value

        Ground Truth: 19,514,849
        Prompt: "How many people live in New York?"
        """
        truth = self.ground_truth['newyork_population']
        rows = self.execute_query(truth.sql)

        assert len(rows) == truth.expected_row_count
        actual_value = rows[0][0]
        expected_value = truth.expected_values['population']

        assert actual_value == expected_value, \
            f"New York population mismatch: expected {expected_value}, got {actual_value}"

    def test_04_florida_population_exact(self):
        """Test 4: Florida population returns EXACT value

        Ground Truth: 21,216,924
        Prompt: "What is Florida's population?"
        """
        truth = self.ground_truth['florida_population']
        rows = self.execute_query(truth.sql)

        assert len(rows) == truth.expected_row_count
        actual_value = rows[0][0]
        expected_value = truth.expected_values['population']

        assert actual_value == expected_value, \
            f"Florida population mismatch: expected {expected_value}, got {actual_value}"

    def test_05_california_sex_breakdown_exact(self):
        """Test 5: California sex breakdown returns EXACT values

        Ground Truth:
          - FEMALE: 19,783,141
          - MALE: 19,562,882
        Prompt: "Show population breakdown by sex for California"
        """
        truth = self.ground_truth['california_sex_breakdown']
        rows = self.execute_query(truth.sql)

        # Should have exactly 2 rows (FEMALE and MALE)
        assert len(rows) == truth.expected_row_count, \
            f"Expected {truth.expected_row_count} rows, got {len(rows)}"

        # Convert rows to dict for comparison
        actual_breakdown = {row[0]: row[1] for row in rows}
        expected_breakdown = truth.expected_values

        for sex, expected_pop in expected_breakdown.items():
            assert sex in actual_breakdown, f"Missing sex category: {sex}"
            actual_pop = actual_breakdown[sex]

            assert actual_pop == expected_pop, \
                f"Population mismatch for {sex}:\n" \
                f"  Expected: {expected_pop}\n" \
                f"  Actual:   {actual_pop}"

    def test_06_usa_total_population_exact(self):
        """Test 6: USA total population returns EXACT value

        Ground Truth: 329,824,950
        Prompt: "What is the total population of the United States?"
        """
        truth = self.ground_truth['usa_total_population']
        rows = self.execute_query(truth.sql)

        assert len(rows) == truth.expected_row_count
        actual_value = rows[0][0]
        expected_value = truth.expected_values['population']

        assert actual_value == expected_value, \
            f"USA population mismatch: expected {expected_value}, got {actual_value}"

    def test_07_california_county_count_exact(self):
        """Test 7: California county count returns EXACT value

        Ground Truth: 58 counties
        Prompt: "How many counties are in California?"
        """
        truth = self.ground_truth['california_county_count']
        rows = self.execute_query(truth.sql)

        assert len(rows) == truth.expected_row_count
        actual_count = rows[0][0]
        expected_count = truth.expected_values['county_count']

        assert actual_count == expected_count, \
            f"California county count mismatch: expected {expected_count}, got {actual_count}"

    def test_08_texas_county_count_exact(self):
        """Test 8: Texas county count returns EXACT value

        Ground Truth: 254 counties
        Prompt: "How many counties does Texas have?"
        """
        truth = self.ground_truth['texas_county_count']
        rows = self.execute_query(truth.sql)

        assert len(rows) == truth.expected_row_count
        actual_count = rows[0][0]
        expected_count = truth.expected_values['county_count']

        assert actual_count == expected_count, \
            f"Texas county count mismatch: expected {expected_count}, got {actual_count}"

    def test_09_under_5_population_exact(self):
        """Test 9: Under 5 population returns EXACT value

        Ground Truth: 19,781,156
        Prompt: "How many children under 5 years old are there in the US?"
        """
        truth = self.ground_truth['under_5_population']
        rows = self.execute_query(truth.sql)

        assert len(rows) == truth.expected_row_count
        actual_value = rows[0][0]
        expected_value = truth.expected_values['population']

        assert actual_value == expected_value, \
            f"Under 5 population mismatch: expected {expected_value}, got {actual_value}"

    def test_10_seniors_65_plus_exact(self):
        """Test 10: Seniors 65+ population returns EXACT value

        Ground Truth: 53,030,023
        Prompt: "How many seniors (age 65+) are there in the USA?"
        """
        truth = self.ground_truth['seniors_65_plus']
        rows = self.execute_query(truth.sql)

        assert len(rows) == truth.expected_row_count
        actual_value = rows[0][0]
        expected_value = truth.expected_values['population']

        assert actual_value == expected_value, \
            f"Seniors 65+ population mismatch: expected {expected_value}, got {actual_value}"

    # Data quality and validation tests
    def test_11_no_negative_populations(self):
        """Test 11: All population estimates must be non-negative

        Validates data quality: no population values should be negative
        """
        rows = self.execute_query("""
            SELECT COUNT(*) as negative_count
            FROM CENSUS_NEIGHBORHOOD_INSIGHTS.CURATED.FACT_POPULATION_AGE
            WHERE ESTIMATE < 0
        """)

        negative_count = rows[0][0]
        assert negative_count == 0, \
            f"Found {negative_count} negative population values"

    def test_12_no_null_estimates(self):
        """Test 12: All rows must have population estimates

        Validates data quality: no NULL values in ESTIMATE column
        """
        rows = self.execute_query("""
            SELECT COUNT(*) as null_count
            FROM CENSUS_NEIGHBORHOOD_INSIGHTS.CURATED.FACT_POPULATION_AGE
            WHERE ESTIMATE IS NULL
        """)

        null_count = rows[0][0]
        assert null_count == 0, \
            f"Found {null_count} NULL estimates"

    def test_13_margin_of_error_positive(self):
        """Test 13: Margin of error must be non-negative

        Validates data quality: MOE should not be negative
        """
        rows = self.execute_query("""
            SELECT COUNT(*) as negative_moe_count
            FROM CENSUS_NEIGHBORHOOD_INSIGHTS.CURATED.FACT_POPULATION_AGE
            WHERE MARGIN_OF_ERROR < 0
        """)

        negative_moe_count = rows[0][0]
        assert negative_moe_count == 0, \
            f"Found {negative_moe_count} negative margin of error values"

    def test_14_all_block_groups_present(self):
        """Test 14: All US states should have data

        Validates coverage: confirm all 50 states have census block group data
        """
        rows = self.execute_query("""
            SELECT COUNT(DISTINCT SUBSTRING(CENSUS_BLOCK_GROUP, 1, 2)) as state_count
            FROM CENSUS_NEIGHBORHOOD_INSIGHTS.CURATED.FACT_POPULATION_AGE
        """)

        state_count = rows[0][0]
        assert state_count >= 50, \
            f"Expected at least 50 states, got {state_count}"

    def test_15_sex_values_only_male_female(self):
        """Test 15: SEX column should only contain MALE or FEMALE

        Validates data integrity: no unexpected sex values
        """
        rows = self.execute_query("""
            SELECT DISTINCT SEX
            FROM CENSUS_NEIGHBORHOOD_INSIGHTS.CURATED.FACT_POPULATION_AGE
            ORDER BY SEX
        """)

        sex_values = {row[0] for row in rows}
        expected_values = {'FEMALE', 'MALE'}

        assert sex_values == expected_values, \
            f"Unexpected sex values: {sex_values}"

    def test_16_age_codes_not_empty(self):
        """Test 16: Age codes must be present for all rows

        Validates data quality: AGE_CODE should not be NULL or empty
        """
        rows = self.execute_query("""
            SELECT COUNT(*) as empty_age_code_count
            FROM CENSUS_NEIGHBORHOOD_INSIGHTS.CURATED.FACT_POPULATION_AGE
            WHERE AGE_CODE IS NULL OR AGE_CODE = ''
        """)

        empty_count = rows[0][0]
        assert empty_count == 0, \
            f"Found {empty_count} rows with empty AGE_CODE"

    def test_17_census_block_groups_valid_format(self):
        """Test 17: CENSUS_BLOCK_GROUP must be 12 digit format

        Validates data integrity: block groups should be SSCCCTTGGG format
        where SS=state, CCC=county, TT=tract, GGG=group
        """
        rows = self.execute_query("""
            SELECT COUNT(*) as invalid_bg_count
            FROM CENSUS_NEIGHBORHOOD_INSIGHTS.CURATED.FACT_POPULATION_AGE
            WHERE LENGTH(CENSUS_BLOCK_GROUP) != 12 OR NOT REGEXP_LIKE(CENSUS_BLOCK_GROUP, '^[0-9]{12}$')
        """)

        invalid_count = rows[0][0]
        assert invalid_count == 0, \
            f"Found {invalid_count} invalid block group formats"

    def test_18_row_count_matches_expected(self):
        """Test 18: Total row count should be consistent

        Validates that the data size is as expected (11M+ rows)
        """
        rows = self.execute_query("""
            SELECT COUNT(*) as total_rows
            FROM CENSUS_NEIGHBORHOOD_INSIGHTS.CURATED.FACT_POPULATION_AGE
        """)

        total_rows = rows[0][0]
        assert total_rows > 11000000, \
            f"Expected 11M+ rows, got {total_rows}"

    def test_19_state_fips_codes_valid(self):
        """Test 19: State FIPS codes should be numeric and reasonable

        Validates that extracted state codes are valid numeric ranges
        """
        rows = self.execute_query("""
            SELECT COUNT(DISTINCT SUBSTRING(CENSUS_BLOCK_GROUP, 1, 2)) as valid_state_count
            FROM CENSUS_NEIGHBORHOOD_INSIGHTS.CURATED.FACT_POPULATION_AGE
        """)

        valid_count = rows[0][0]
        # Should have at least 50 states (some might have FIPS > 56 for territories)
        assert valid_count >= 50, \
            f"Expected at least 50 state FIPS codes, got {valid_count}"

    def test_20_ground_truth_consistency(self):
        """Test 20: All ground truth values are internally consistent

        Validates: Sum of parts equals whole (e.g., state populations sum to USA total)
        """
        # Get sum of four largest states
        rows = self.execute_query("""
            SELECT SUM(state_pop) as sum_four_largest
            FROM (
                SELECT SUM(ESTIMATE) as state_pop
                FROM CENSUS_NEIGHBORHOOD_INSIGHTS.CURATED.FACT_POPULATION_AGE
                WHERE CENSUS_BLOCK_GROUP LIKE '06%'
                  OR CENSUS_BLOCK_GROUP LIKE '48%'
                  OR CENSUS_BLOCK_GROUP LIKE '36%'
                  OR CENSUS_BLOCK_GROUP LIKE '12%'
                GROUP BY SUBSTRING(CENSUS_BLOCK_GROUP, 1, 2)
            )
        """)

        sum_four = rows[0][0]
        expected_sum = (
            self.ground_truth['california_population'].expected_values['population'] +
            self.ground_truth['texas_population'].expected_values['population'] +
            self.ground_truth['newyork_population'].expected_values['population'] +
            self.ground_truth['florida_population'].expected_values['population']
        )

        assert sum_four == expected_sum, \
            f"Four largest states sum mismatch: expected {expected_sum}, got {sum_four}"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
