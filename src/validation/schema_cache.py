"""Cache Snowflake metadata with TTL-based refresh"""

import logging
from datetime import datetime, timedelta
from typing import List
from src.validation.schema_metadata import SemanticMetadataProvider

logger = logging.getLogger(__name__)


class SemanticMetadataCache:
    """
    Cache Snowflake metadata with automatic refresh

    Usage:
        cache = SemanticMetadataCache(refresh_minutes=60)
        grain = cache.get_grain('FACT_POPULATION_AGE')
    """

    def __init__(self, refresh_minutes: int = 60):
        self.provider = SemanticMetadataProvider()
        self.refresh_minutes = refresh_minutes
        self.cache = {}
        self.last_refresh = None
        self.logger = logger

    def get_grain(self, table_name: str) -> List[str]:
        """Get grain with automatic refresh if stale"""
        self._ensure_fresh_cache()
        key = f"grain:{table_name}"

        if key not in self.cache:
            self.logger.info(f"Cache miss for grain of {table_name}")
            grain = self.provider.get_fact_table_grain(table_name)
            self.cache[key] = grain

        return self.cache[key]

    def get_row_count(self, table_name: str) -> int:
        """Get row count with automatic refresh if stale"""
        self._ensure_fresh_cache()
        key = f"row_count:{table_name}"

        if key not in self.cache:
            self.logger.info(f"Cache miss for row count of {table_name}")
            count = self.provider.get_table_row_count(table_name)
            self.cache[key] = count

        return self.cache[key]

    def get_distinct_count(self, table_name: str, column_name: str) -> int:
        """Get distinct count for cardinality calculation"""
        self._ensure_fresh_cache()
        key = f"distinct:{table_name}:{column_name}"

        if key not in self.cache:
            self.logger.info(f"Cache miss for distinct count {table_name}.{column_name}")
            count = self.provider.get_distinct_count(table_name, column_name)
            self.cache[key] = count

        return self.cache[key]

    def _ensure_fresh_cache(self):
        """Refresh cache if older than TTL"""
        if self.last_refresh is None:
            self.logger.info("Initial cache population")
            self._refresh()
        else:
            age = (datetime.now() - self.last_refresh).total_seconds() / 60
            if age > self.refresh_minutes:
                self.logger.info(f"Cache stale (age: {age:.1f}m), refreshing")
                self._refresh()

    def _refresh(self):
        """Populate cache with common lookups"""
        try:
            # Pre-populate grain for fact tables
            fact_tables = [
                'FACT_POPULATION_AGE',
                'FACT_RACE_ETHNICITY',
                'FACT_HOUSEHOLD_COMPOSITION'
            ]

            for table in fact_tables:
                key = f"grain:{table}"
                self.cache[key] = self.provider.get_fact_table_grain(table)

                key = f"row_count:{table}"
                self.cache[key] = self.provider.get_table_row_count(table)

            self.last_refresh = datetime.now()
            self.logger.info("Cache refresh complete")
        except Exception as e:
            self.logger.error(f"Cache refresh failed: {e}")
            raise
