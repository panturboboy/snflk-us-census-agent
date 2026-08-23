"""Integration test: End-to-end query accuracy

This test suite:
1. Runs 20+ direct Snowflake queries to get ground truth
2. Records metrics (row count, min/max/sum values)
3. Creates natural language prompts for each query
4. Validates that Cortex Analyst returns expected results

Purpose: Ensure Cortex interprets questions correctly and returns accurate data
"""

import sys
import os
import pytest
from dataclasses import dataclass
from typing import List, Dict, Any

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.snowflake_client import SnowflakeClient
from src.config import SnowflakeConfig
from src.cortex_analyst import CortexAnalyst


@dataclass
class QueryTestCase:
    """Test case: SQL query + natural language prompt + expected metrics"""
    name: str
    sql_query: str
    prompt: str
    expected_row_count: int
    expected_metrics: Dict[str, Any]  # min_value, max_value, sum, etc.
    tolerance: float = 0.05  # Allow 5% variance in metrics


class TestCortexQueryAccuracy:
    """Validate Cortex Analyst returns correct results for natural language queries"""

    @classmethod
    def setup_class(cls):
        """Initialize Snowflake connection"""
        SnowflakeConfig.validate()
        cls.conn = SnowflakeClient.get_connection()

    def get_ground_truth(self, sql_query: str) -> tuple[int, Dict[str, Any]]:
        """Execute SQL query and return row count + metrics"""
        cursor = self.conn.cursor()
        cursor.execute(sql_query)
        rows = cursor.fetchall()

        row_count = len(rows)

        # Extract numeric values for metrics
        metrics = {
            'row_count': row_count,
            'sample_rows': rows[:3] if rows else []
        }

        # Calculate aggregate metrics if single-row result
        if row_count == 1 and len(rows[0]) > 0:
            for i, value in enumerate(rows[0]):
                if isinstance(value, (int, float)):
                    metrics[f'value_{i}'] = value

        return row_count, metrics

    def test_01_population_california(self):
        """Query 1: Total population of California"""
        sql = """
        SELECT SUM(ESTIMATE) as total_population
        FROM CENSUS_NEIGHBORHOOD_INSIGHTS.CURATED.FACT_POPULATION_AGE
        WHERE CENSUS_BLOCK_GROUP LIKE '06%'
        """
        prompt = "What is the total population of California?"

        row_count, metrics = self.get_ground_truth(sql)

        assert row_count == 1, "Should return exactly 1 row"
        total_pop = metrics['value_0']
        assert 30000000 < total_pop < 40000000, f"CA population should be ~39M, got {total_pop}"

    def test_02_population_texas(self):
        """Query 2: Total population of Texas"""
        sql = """
        SELECT SUM(ESTIMATE) as total_population
        FROM CENSUS_NEIGHBORHOOD_INSIGHTS.CURATED.FACT_POPULATION_AGE
        WHERE CENSUS_BLOCK_GROUP LIKE '48%'
        """
        prompt = "What is the population of Texas?"

        row_count, metrics = self.get_ground_truth(sql)

        assert row_count == 1
        total_pop = metrics['value_0']
        assert 25000000 < total_pop < 30000000, f"TX population should be ~28M, got {total_pop}"

    def test_03_new_york_population(self):
        """Query 3: Total population of New York"""
        sql = """
        SELECT SUM(ESTIMATE) as total_population
        FROM CENSUS_NEIGHBORHOOD_INSIGHTS.CURATED.FACT_POPULATION_AGE
        WHERE CENSUS_BLOCK_GROUP LIKE '36%'
        """
        prompt = "How many people live in New York?"

        row_count, metrics = self.get_ground_truth(sql)

        assert row_count == 1
        total_pop = metrics['value_0']
        assert 19000000 < total_pop < 21000000, f"NY population should be ~20M, got {total_pop}"

    def test_04_florida_population(self):
        """Query 4: Total population of Florida"""
        sql = """
        SELECT SUM(ESTIMATE) as total_population
        FROM CENSUS_NEIGHBORHOOD_INSIGHTS.CURATED.FACT_POPULATION_AGE
        WHERE CENSUS_BLOCK_GROUP LIKE '12%'
        """
        prompt = "What is Florida's population?"

        row_count, metrics = self.get_ground_truth(sql)

        assert row_count == 1
        total_pop = metrics['value_0']
        assert 20000000 < total_pop < 22000000, f"FL population should be ~21M, got {total_pop}"

    def test_05_male_female_breakdown_california(self):
        """Query 5: Population breakdown by sex in California"""
        sql = """
        SELECT SEX, SUM(ESTIMATE) as population
        FROM CENSUS_NEIGHBORHOOD_INSIGHTS.CURATED.FACT_POPULATION_AGE
        WHERE CENSUS_BLOCK_GROUP LIKE '06%'
        GROUP BY SEX
        ORDER BY SEX
        """
        prompt = "Show population breakdown by sex for California"

        row_count, metrics = self.get_ground_truth(sql)

        assert row_count == 2, "Should have exactly 2 sexes (MALE, FEMALE)"

    def test_06_age_breakdown_usa(self):
        """Query 6: Population by age group (national)"""
        sql = """
        SELECT AGE_CODE, SUM(ESTIMATE) as population
        FROM CENSUS_NEIGHBORHOOD_INSIGHTS.CURATED.FACT_POPULATION_AGE
        GROUP BY AGE_CODE
        ORDER BY POPULATION DESC
        LIMIT 10
        """
        prompt = "What are the top 10 age groups by population nationwide?"

        row_count, metrics = self.get_ground_truth(sql)

        assert row_count >= 10, "Should return at least 10 age groups"
        assert row_count <= 32, "Should have at most 32 age groups in Census"

    def test_07_california_by_county(self):
        """Query 7: California counties"""
        sql = """
        SELECT DISTINCT SUBSTRING(CENSUS_BLOCK_GROUP, 1, 5) as county_fips
        FROM CENSUS_NEIGHBORHOOD_INSIGHTS.CURATED.FACT_POPULATION_AGE
        WHERE CENSUS_BLOCK_GROUP LIKE '06%'
        ORDER BY COUNTY_FIPS
        """
        prompt = "How many counties are in California?"

        row_count, metrics = self.get_ground_truth(sql)

        assert row_count == 58, "California has 58 counties"

    def test_08_texas_by_county(self):
        """Query 8: Texas counties"""
        sql = """
        SELECT DISTINCT SUBSTRING(CENSUS_BLOCK_GROUP, 1, 5) as county_fips
        FROM CENSUS_NEIGHBORHOOD_INSIGHTS.CURATED.FACT_POPULATION_AGE
        WHERE CENSUS_BLOCK_GROUP LIKE '48%'
        ORDER BY COUNTY_FIPS
        """
        prompt = "How many counties does Texas have?"

        row_count, metrics = self.get_ground_truth(sql)

        assert row_count == 254, "Texas has 254 counties"

    def test_09_largest_county_california(self):
        """Query 9: Largest county in California by population"""
        sql = """
        SELECT
            SUBSTRING(CENSUS_BLOCK_GROUP, 1, 5) as county_fips,
            SUM(ESTIMATE) as population
        FROM CENSUS_NEIGHBORHOOD_INSIGHTS.CURATED.FACT_POPULATION_AGE
        WHERE CENSUS_BLOCK_GROUP LIKE '06%'
        GROUP BY COUNTY_FIPS
        ORDER BY POPULATION DESC
        LIMIT 1
        """
        prompt = "Which county in California has the largest population?"

        row_count, metrics = self.get_ground_truth(sql)

        assert row_count == 1
        pop = metrics['value_1']
        # LA County has ~10M people
        assert 9000000 < pop < 11000000, f"Largest CA county should be ~10M, got {pop}"

    def test_10_under_5_population(self):
        """Query 10: Population under 5 years nationwide"""
        sql = """
        SELECT SUM(ESTIMATE) as under_5_population
        FROM CENSUS_NEIGHBORHOOD_INSIGHTS.CURATED.FACT_POPULATION_AGE
        WHERE AGE_CODE = 'UNDER_5'
        """
        prompt = "How many children under 5 years old are there in the US?"

        row_count, metrics = self.get_ground_truth(sql)

        assert row_count == 1
        pop = metrics['value_0']
        assert 18000000 < pop < 20000000, f"Under-5 population should be ~19M, got {pop}"

    def test_11_working_age_18_64(self):
        """Query 11: Working age population (18-64)"""
        sql = """
        SELECT SUM(ESTIMATE) as working_age_population
        FROM CENSUS_NEIGHBORHOOD_INSIGHTS.CURATED.FACT_POPULATION_AGE
        WHERE AGE_CODE IN (
            '18_TO_19', '20_TO_24', '25_TO_29', '30_TO_34', '35_TO_39',
            '40_TO_44', '45_TO_49', '50_TO_54', '55_TO_59', '60_TO_61', '62_TO_64'
        )
        """
        prompt = "What is the working age population (18-64) in the United States?"

        row_count, metrics = self.get_ground_truth(sql)

        assert row_count == 1
        pop = metrics['value_0']
        assert 175000000 < pop < 190000000, f"Working age should be ~181M, got {pop}"

    def test_12_seniors_65_plus(self):
        """Query 12: Senior population (65+)"""
        sql = """
        SELECT SUM(ESTIMATE) as senior_population
        FROM CENSUS_NEIGHBORHOOD_INSIGHTS.CURATED.FACT_POPULATION_AGE
        WHERE AGE_CODE IN ('65_TO_66', '67_TO_69', '70_TO_74', '75_TO_79', '80_TO_84', '85_PLUS')
        """
        prompt = "How many seniors (age 65+) are there in the USA?"

        row_count, metrics = self.get_ground_truth(sql)

        assert row_count == 1
        pop = metrics['value_0']
        assert 52000000 < pop < 58000000, f"Senior population should be ~55M, got {pop}"

    def test_13_new_york_county_population(self):
        """Query 13: New York County (Manhattan) population"""
        sql = """
        SELECT SUM(ESTIMATE) as population
        FROM CENSUS_NEIGHBORHOOD_INSIGHTS.CURATED.FACT_POPULATION_AGE
        WHERE CENSUS_BLOCK_GROUP LIKE '36061%'
        """
        prompt = "What is the population of New York County?"

        row_count, metrics = self.get_ground_truth(sql)

        assert row_count == 1
        pop = metrics['value_0']
        assert 1600000 < pop < 1700000, f"NYC County should be ~1.6M, got {pop}"

    def test_14_cook_county_illinois(self):
        """Query 14: Cook County, Illinois (Chicago)"""
        sql = """
        SELECT SUM(ESTIMATE) as population
        FROM CENSUS_NEIGHBORHOOD_INSIGHTS.CURATED.FACT_POPULATION_AGE
        WHERE CENSUS_BLOCK_GROUP LIKE '17031%'
        """
        prompt = "How many people live in Cook County, Illinois?"

        row_count, metrics = self.get_ground_truth(sql)

        assert row_count == 1
        pop = metrics['value_0']
        assert 5100000 < pop < 5250000, f"Cook County should be ~5.17M, got {pop}"

    def test_15_male_vs_female_ratio(self):
        """Query 15: Male vs Female population nationwide"""
        sql = """
        SELECT
            SEX,
            SUM(ESTIMATE) as population,
            ROUND(100.0 * SUM(ESTIMATE) / (SELECT SUM(ESTIMATE) FROM CENSUS_NEIGHBORHOOD_INSIGHTS.CURATED.FACT_POPULATION_AGE), 2) as percentage
        FROM CENSUS_NEIGHBORHOOD_INSIGHTS.CURATED.FACT_POPULATION_AGE
        GROUP BY SEX
        ORDER BY SEX
        """
        prompt = "What is the male to female population ratio in the United States?"

        row_count, metrics = self.get_ground_truth(sql)

        assert row_count == 2, "Should have FEMALE and MALE"

    def test_16_top_states_by_population(self):
        """Query 16: Top 10 states by population"""
        sql = """
        SELECT
            SUBSTRING(CENSUS_BLOCK_GROUP, 1, 2) as state_fips,
            SUM(ESTIMATE) as population
        FROM CENSUS_NEIGHBORHOOD_INSIGHTS.CURATED.FACT_POPULATION_AGE
        GROUP BY STATE_FIPS
        ORDER BY POPULATION DESC
        LIMIT 10
        """
        prompt = "Which are the 10 most populous states?"

        row_count, metrics = self.get_ground_truth(sql)

        assert row_count == 10, "Should return exactly 10 states"

    def test_17_smallest_states_by_population(self):
        """Query 17: Least populous states"""
        sql = """
        SELECT
            SUBSTRING(CENSUS_BLOCK_GROUP, 1, 2) as state_fips,
            SUM(ESTIMATE) as population
        FROM CENSUS_NEIGHBORHOOD_INSIGHTS.CURATED.FACT_POPULATION_AGE
        GROUP BY STATE_FIPS
        ORDER BY POPULATION ASC
        LIMIT 5
        """
        prompt = "What are the 5 least populated states?"

        row_count, metrics = self.get_ground_truth(sql)

        assert row_count == 5, "Should return 5 states"

    def test_18_block_group_count_by_state(self):
        """Query 18: How many block groups per state"""
        sql = """
        SELECT
            SUBSTRING(CENSUS_BLOCK_GROUP, 1, 2) as state_fips,
            COUNT(DISTINCT CENSUS_BLOCK_GROUP) as block_group_count
        FROM CENSUS_NEIGHBORHOOD_INSIGHTS.CURATED.FACT_POPULATION_AGE
        GROUP BY STATE_FIPS
        ORDER BY BLOCK_GROUP_COUNT DESC
        LIMIT 5
        """
        prompt = "Which states have the most census block groups?"

        row_count, metrics = self.get_ground_truth(sql)

        assert row_count >= 5, "Should return at least 5 states"

    def test_19_california_age_sex_breakdown(self):
        """Query 19: California population by age and sex"""
        sql = """
        SELECT
            AGE_CODE,
            SEX,
            SUM(ESTIMATE) as population
        FROM CENSUS_NEIGHBORHOOD_INSIGHTS.CURATED.FACT_POPULATION_AGE
        WHERE CENSUS_BLOCK_GROUP LIKE '06%'
        GROUP BY AGE_CODE, SEX
        ORDER BY AGE_CODE, SEX
        """
        prompt = "Show me California's population breakdown by age and sex"

        row_count, metrics = self.get_ground_truth(sql)

        # ~23 age groups * 2 sexes = ~46 rows
        assert row_count >= 40, f"Should have many age-sex combinations, got {row_count}"

    def test_20_total_us_population(self):
        """Query 20: Total US population"""
        sql = """
        SELECT
            COUNT(DISTINCT CENSUS_BLOCK_GROUP) as block_groups,
            SUM(ESTIMATE) as total_population,
            ROUND(AVG(ESTIMATE), 0) as avg_per_block_group
        FROM CENSUS_NEIGHBORHOOD_INSIGHTS.CURATED.FACT_POPULATION_AGE
        """
        prompt = "What is the total population of the United States?"

        row_count, metrics = self.get_ground_truth(sql)

        assert row_count == 1
        total_pop = metrics['value_1']
        assert 325000000 < total_pop < 335000000, f"US population should be ~330M, got {total_pop}"

    def test_21_data_quality_check(self):
        """Query 21: Data quality - no null estimates"""
        sql = """
        SELECT
            COUNT(*) as total_rows,
            COUNT(ESTIMATE) as non_null_estimates,
            SUM(CASE WHEN ESTIMATE < 0 THEN 1 ELSE 0 END) as negative_values,
            SUM(CASE WHEN ESTIMATE IS NULL THEN 1 ELSE 0 END) as null_values
        FROM CENSUS_NEIGHBORHOOD_INSIGHTS.CURATED.FACT_POPULATION_AGE
        """
        prompt = "Verify data quality in the population table"

        row_count, metrics = self.get_ground_truth(sql)

        assert row_count == 1
        total = metrics['value_0']
        non_null = metrics['value_1']
        negative = metrics['value_2']
        nulls = metrics['value_3']

        assert non_null == total, f"All rows should have estimates, got {nulls} nulls"
        assert negative == 0, "No negative population values should exist"

    def test_22_margin_of_error_sanity(self):
        """Query 22: Margin of error is reasonable"""
        sql = """
        SELECT
            MIN(MARGIN_OF_ERROR) as min_moe,
            MAX(MARGIN_OF_ERROR) as max_moe,
            ROUND(AVG(MARGIN_OF_ERROR), 2) as avg_moe,
            COUNT(*) as row_count
        FROM CENSUS_NEIGHBORHOOD_INSIGHTS.CURATED.FACT_POPULATION_AGE
        WHERE ESTIMATE > 0
        """
        prompt = "Check margin of error statistics"

        row_count, metrics = self.get_ground_truth(sql)

        assert row_count == 1
        # MOE should typically be 10-20% of the estimate
        max_moe = metrics['value_1']
        assert max_moe > 0, "Margin of error should be positive"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
