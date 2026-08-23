"""
Ground Truth Fixtures - Exact values from Snowflake

This module captures EXACT values from direct Snowflake queries.
These are the source of truth for all integration tests.

Run once to generate, then use for all test validations.
"""

import sys
import os
from dataclasses import dataclass
from typing import Dict, Any

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.snowflake_client import SnowflakeClient
from src.config import SnowflakeConfig


@dataclass
class QueryGroundTruth:
    """Ground truth for a single query"""
    name: str
    prompt: str
    sql: str
    expected_row_count: int
    expected_values: Dict[str, Any]


def capture_ground_truth() -> Dict[str, QueryGroundTruth]:
    """Capture exact ground truth from Snowflake"""
    SnowflakeConfig.validate()
    conn = SnowflakeClient.get_connection()
    cursor = conn.cursor()

    ground_truth = {}

    # Query 1: California population
    cursor.execute("""
        SELECT SUM(ESTIMATE) as total_population
        FROM CENSUS_NEIGHBORHOOD_INSIGHTS.CURATED.FACT_POPULATION_AGE
        WHERE CENSUS_BLOCK_GROUP LIKE '06%'
    """)
    row = cursor.fetchone()
    ground_truth['california_population'] = QueryGroundTruth(
        name='California Population',
        prompt='What is the total population of California?',
        sql='SELECT SUM(ESTIMATE) FROM FACT_POPULATION_AGE WHERE CENSUS_BLOCK_GROUP LIKE \'06%\'',
        expected_row_count=1,
        expected_values={'population': row[0]}
    )

    # Query 2: Texas population
    cursor.execute("""
        SELECT SUM(ESTIMATE) as total_population
        FROM CENSUS_NEIGHBORHOOD_INSIGHTS.CURATED.FACT_POPULATION_AGE
        WHERE CENSUS_BLOCK_GROUP LIKE '48%'
    """)
    row = cursor.fetchone()
    ground_truth['texas_population'] = QueryGroundTruth(
        name='Texas Population',
        prompt='What is the population of Texas?',
        sql='SELECT SUM(ESTIMATE) FROM FACT_POPULATION_AGE WHERE CENSUS_BLOCK_GROUP LIKE \'48%\'',
        expected_row_count=1,
        expected_values={'population': row[0]}
    )

    # Query 3: New York population
    cursor.execute("""
        SELECT SUM(ESTIMATE) as total_population
        FROM CENSUS_NEIGHBORHOOD_INSIGHTS.CURATED.FACT_POPULATION_AGE
        WHERE CENSUS_BLOCK_GROUP LIKE '36%'
    """)
    row = cursor.fetchone()
    ground_truth['newyork_population'] = QueryGroundTruth(
        name='New York Population',
        prompt='How many people live in New York?',
        sql='SELECT SUM(ESTIMATE) FROM FACT_POPULATION_AGE WHERE CENSUS_BLOCK_GROUP LIKE \'36%\'',
        expected_row_count=1,
        expected_values={'population': row[0]}
    )

    # Query 4: Florida population
    cursor.execute("""
        SELECT SUM(ESTIMATE) as total_population
        FROM CENSUS_NEIGHBORHOOD_INSIGHTS.CURATED.FACT_POPULATION_AGE
        WHERE CENSUS_BLOCK_GROUP LIKE '12%'
    """)
    row = cursor.fetchone()
    ground_truth['florida_population'] = QueryGroundTruth(
        name='Florida Population',
        prompt='What is Florida\'s population?',
        sql='SELECT SUM(ESTIMATE) FROM FACT_POPULATION_AGE WHERE CENSUS_BLOCK_GROUP LIKE \'12%\'',
        expected_row_count=1,
        expected_values={'population': row[0]}
    )

    # Query 5: Sex breakdown California
    cursor.execute("""
        SELECT SEX, SUM(ESTIMATE) as population
        FROM CENSUS_NEIGHBORHOOD_INSIGHTS.CURATED.FACT_POPULATION_AGE
        WHERE CENSUS_BLOCK_GROUP LIKE '06%'
        GROUP BY SEX
        ORDER BY SEX
    """)
    rows = cursor.fetchall()
    sex_breakdown = {row[0]: row[1] for row in rows}
    ground_truth['california_sex_breakdown'] = QueryGroundTruth(
        name='California Sex Breakdown',
        prompt='Show population breakdown by sex for California',
        sql='SELECT SEX, SUM(ESTIMATE) FROM FACT_POPULATION_AGE WHERE CENSUS_BLOCK_GROUP LIKE \'06%\' GROUP BY SEX',
        expected_row_count=2,
        expected_values=sex_breakdown
    )

    # Query 6: Total US population
    cursor.execute("""
        SELECT SUM(ESTIMATE) as total_population
        FROM CENSUS_NEIGHBORHOOD_INSIGHTS.CURATED.FACT_POPULATION_AGE
    """)
    row = cursor.fetchone()
    ground_truth['usa_total_population'] = QueryGroundTruth(
        name='USA Total Population',
        prompt='What is the total population of the United States?',
        sql='SELECT SUM(ESTIMATE) FROM FACT_POPULATION_AGE',
        expected_row_count=1,
        expected_values={'population': row[0]}
    )

    # Query 7: California counties
    cursor.execute("""
        SELECT COUNT(DISTINCT SUBSTRING(CENSUS_BLOCK_GROUP, 1, 5)) as county_count
        FROM CENSUS_NEIGHBORHOOD_INSIGHTS.CURATED.FACT_POPULATION_AGE
        WHERE CENSUS_BLOCK_GROUP LIKE '06%'
    """)
    row = cursor.fetchone()
    ground_truth['california_county_count'] = QueryGroundTruth(
        name='California County Count',
        prompt='How many counties are in California?',
        sql='SELECT COUNT(DISTINCT SUBSTRING(CENSUS_BLOCK_GROUP, 1, 5)) FROM FACT_POPULATION_AGE WHERE CENSUS_BLOCK_GROUP LIKE \'06%\'',
        expected_row_count=1,
        expected_values={'county_count': row[0]}
    )

    # Query 8: Texas counties
    cursor.execute("""
        SELECT COUNT(DISTINCT SUBSTRING(CENSUS_BLOCK_GROUP, 1, 5)) as county_count
        FROM CENSUS_NEIGHBORHOOD_INSIGHTS.CURATED.FACT_POPULATION_AGE
        WHERE CENSUS_BLOCK_GROUP LIKE '48%'
    """)
    row = cursor.fetchone()
    ground_truth['texas_county_count'] = QueryGroundTruth(
        name='Texas County Count',
        prompt='How many counties does Texas have?',
        sql='SELECT COUNT(DISTINCT SUBSTRING(CENSUS_BLOCK_GROUP, 1, 5)) FROM FACT_POPULATION_AGE WHERE CENSUS_BLOCK_GROUP LIKE \'48%\'',
        expected_row_count=1,
        expected_values={'county_count': row[0]}
    )

    # Query 9: Under 5 population
    cursor.execute("""
        SELECT SUM(ESTIMATE) as population
        FROM CENSUS_NEIGHBORHOOD_INSIGHTS.CURATED.FACT_POPULATION_AGE
        WHERE AGE_CODE = 'UNDER_5'
    """)
    row = cursor.fetchone()
    ground_truth['under_5_population'] = QueryGroundTruth(
        name='Under 5 Population',
        prompt='How many children under 5 years old are there in the US?',
        sql='SELECT SUM(ESTIMATE) FROM FACT_POPULATION_AGE WHERE AGE_CODE = \'UNDER_5\'',
        expected_row_count=1,
        expected_values={'population': row[0]}
    )

    # Query 10: Seniors 65+
    cursor.execute("""
        SELECT SUM(ESTIMATE) as population
        FROM CENSUS_NEIGHBORHOOD_INSIGHTS.CURATED.FACT_POPULATION_AGE
        WHERE AGE_CODE IN ('65_TO_66', '67_TO_69', '70_TO_74', '75_TO_79', '80_TO_84', '85_PLUS')
    """)
    row = cursor.fetchone()
    ground_truth['seniors_65_plus'] = QueryGroundTruth(
        name='Seniors 65+',
        prompt='How many seniors (age 65+) are there in the USA?',
        sql='SELECT SUM(ESTIMATE) FROM FACT_POPULATION_AGE WHERE AGE_CODE IN (\'65_TO_66\', \'67_TO_69\', \'70_TO_74\', \'75_TO_79\', \'80_TO_84\', \'85_PLUS\')',
        expected_row_count=1,
        expected_values={'population': row[0]}
    )

    return ground_truth


def print_ground_truth():
    """Print all ground truth values"""
    print("\n" + "=" * 80)
    print("GROUND TRUTH - EXACT VALUES FROM SNOWFLAKE")
    print("=" * 80)

    ground_truth = capture_ground_truth()

    for key, truth in ground_truth.items():
        print(f"\n{truth.name}")
        print(f"  Key: {key}")
        print(f"  Prompt: {truth.prompt}")
        print(f"  Expected Rows: {truth.expected_row_count}")
        print(f"  Expected Values: {truth.expected_values}")

    print("\n" + "=" * 80)
    print(f"Total test cases: {len(ground_truth)}")
    print("=" * 80 + "\n")

    return ground_truth


if __name__ == '__main__':
    print_ground_truth()
