"""Validate query grain against fact table grain"""

import logging
from typing import List
from dataclasses import dataclass
from src.validation.schema_cache import SemanticMetadataCache
from src.validation.query_parser import QueryStructure

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of a validation check"""
    status: str  # 'PASS', 'FAIL', 'WARN'
    message: str = ""
    details: dict = None

    def __post_init__(self):
        if self.details is None:
            self.details = {}

    @staticmethod
    def pass_result(message: str = ""):
        return ValidationResult(status='PASS', message=message)

    @staticmethod
    def fail_result(message: str):
        return ValidationResult(status='FAIL', message=message)

    @staticmethod
    def warn_result(message: str):
        return ValidationResult(status='WARN', message=message)


class GrainValidator:
    """
    Validate query grain using Snowflake metadata

    Grain = the primary key of a fact table
    Check: Does the query GROUP BY match the fact table grain?
    """

    def __init__(self, metadata_cache: SemanticMetadataCache):
        self.cache = metadata_cache
        self.logger = logger

    def validate(self, parsed_query: QueryStructure) -> ValidationResult:
        """
        Check if query's GROUP BY matches fact table grain

        Example:
            Fact table: FACT_POPULATION_AGE
            Grain: ['CENSUS_BLOCK_GROUP', 'AGE_ID', 'SEX']
            Query GROUP BY: ['CENSUS_BLOCK_GROUP', 'AGE_ID', 'SEX']
            Result: ✅ PASS

        Example:
            Fact table: FACT_POPULATION_AGE
            Grain: ['CENSUS_BLOCK_GROUP', 'AGE_ID', 'SEX']
            Query GROUP BY: ['STATE', 'AGE_GROUP']
            Result: ❌ FAIL (missing CENSUS_BLOCK_GROUP)
        """

        if not parsed_query.tables_accessed:
            self.logger.info("No tables accessed, skipping grain validation")
            return ValidationResult.pass_result("No tables to validate grain for")

        for table in parsed_query.tables_accessed:
            # Skip dimension tables (only validate fact tables)
            if table.startswith('DIM_'):
                self.logger.debug(f"Skipping grain check for dimension table {table}")
                continue

            # Get grain from Snowflake
            grain = self.cache.get_grain(table)

            if not grain:
                self.logger.warning(f"Could not get grain for {table}, skipping validation")
                continue

            self.logger.info(f"Validating grain for {table}: {grain}")

            group_by = [col.upper() for col in (parsed_query.group_by_columns or [])]

            # Check if GROUP BY matches grain
            if not self._grain_matches(grain, group_by):
                missing = set(grain) - set(group_by)
                return ValidationResult.fail_result(
                    f"Grain mismatch for {table}: "
                    f"fact grain is {grain}, "
                    f"but query groups by {group_by}. "
                    f"Missing: {list(missing)}"
                )

            self.logger.info(f"✅ Grain valid for {table}")

        return ValidationResult.pass_result("All grain validations passed")

    def _grain_matches(self, grain: List[str], group_by: List[str]) -> bool:
        """
        Check if GROUP BY satisfies fact table grain

        Grain matches if:
        1. GROUP BY contains all grain columns (exact match) → Valid aggregation
        2. No GROUP BY → Single-row aggregation (SUM over entire table) → Valid
        3. GROUP BY subset of grain → Invalid! (data will be implicitly aggregated)

        Example:
            Grain: [BLOCK_GROUP, AGE_ID, SEX]
            GROUP BY: [BLOCK_GROUP, AGE_ID, SEX] → ✅ PASS (exact)
            GROUP BY: [BLOCK_GROUP, AGE_ID] → ❌ FAIL (implicit aggregation over SEX)
            GROUP BY: [] (implicit SUM) → ✅ PASS (single row)
        """

        grain_set = set(col.upper() for col in grain)
        group_by_set = set(col.upper() for col in group_by) if group_by else set()

        # No GROUP BY = single-row aggregation = OK
        if not group_by_set:
            return True

        # GROUP BY must contain all grain columns
        # (Roll-up: we aggregate at the grain level, then further up)
        return grain_set.issubset(group_by_set)
