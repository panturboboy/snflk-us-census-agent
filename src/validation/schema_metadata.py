"""Query Snowflake semantic metadata"""

import logging
from typing import List, Dict
from src.snowflake_client import SnowflakeClient

logger = logging.getLogger(__name__)


class SemanticMetadataProvider:
    """Query Snowflake's semantic metadata from INFORMATION_SCHEMA"""

    def get_fact_table_grain(self, table_name: str) -> List[str]:
        """
        Get primary key (grain) for a fact table

        Example result for FACT_POPULATION_AGE:
        ['CENSUS_BLOCK_GROUP', 'AGE_ID', 'SEX']
        """
        try:
            query = f"""
            SELECT COLUMN_NAME
            FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
            WHERE TABLE_NAME = '{table_name}'
              AND TABLE_SCHEMA = 'CURATED'
              AND CONSTRAINT_TYPE = 'PRIMARY KEY'
            ORDER BY ORDINAL_POSITION;
            """
            results = SnowflakeClient.query(query)
            grain = [row['COLUMN_NAME'] for row in results]
            logger.debug(f"Grain for {table_name}: {grain}")
            return grain
        except Exception as e:
            logger.error(f"Failed to get grain for {table_name}: {e}")
            return []

    def get_table_row_count(self, table_name: str) -> int:
        """Get approximate row count from table statistics"""
        try:
            query = f"""
            SELECT ROW_COUNT
            FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_NAME = '{table_name}'
              AND TABLE_SCHEMA = 'CURATED';
            """
            results = SnowflakeClient.query(query)
            if results:
                count = results[0].get('ROW_COUNT', 0)
                logger.debug(f"Row count for {table_name}: {count}")
                return count
            return 0
        except Exception as e:
            logger.error(f"Failed to get row count for {table_name}: {e}")
            return 0

    def get_distinct_count(self, table_name: str, column_name: str) -> int:
        """Get distinct value count for cardinality calculation"""
        try:
            query = f"""
            SELECT COUNT(DISTINCT {column_name}) as distinct_count
            FROM CURATED.{table_name};
            """
            results = SnowflakeClient.query(query)
            if results:
                count = results[0].get('DISTINCT_COUNT', 0)
                logger.debug(f"Distinct count for {table_name}.{column_name}: {count}")
                return count
            return 0
        except Exception as e:
            logger.error(f"Failed to get distinct count: {e}")
            return 0

    def get_relationships(self) -> List[Dict]:
        """Get relationship definitions from semantic model"""
        try:
            query = """
            SELECT
                RELATIONSHIP_NAME,
                FROM_TABLE_NAME,
                TO_TABLE_NAME,
                FROM_COLUMN_NAME,
                TO_COLUMN_NAME
            FROM INFORMATION_SCHEMA.SEMANTIC_MODEL_RELATIONSHIPS
            WHERE SEMANTIC_MODEL_NAME = 'CENSUS_DEMOGRAPHICS_MODEL';
            """
            relationships = SnowflakeClient.query(query)
            logger.debug(f"Found {len(relationships)} relationships")
            return relationships
        except Exception as e:
            logger.error(f"Failed to get relationships: {e}")
            return []
