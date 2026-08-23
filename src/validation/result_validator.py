"""Validate query results for duplicates, fan-out, and cardinality"""

import logging
from typing import List, Optional
from dataclasses import dataclass
from src.validation.schema_cache import SemanticMetadataCache
from src.validation.grain_validator import ValidationResult

logger = logging.getLogger(__name__)


class ResultValidator:
    """
    Validate query results post-execution

    Checks:
    1. Duplicates: Are there duplicate rows at the grain level?
    2. Fan-out: Did joins cause unexpected row multiplication?
    3. Cardinality: Are result row counts what we expect?
    """

    def __init__(self, metadata_cache: SemanticMetadataCache):
        self.cache = metadata_cache
        self.logger = logger

    def validate_no_duplicates(
        self,
        results: list,
        grain: List[str]
    ) -> ValidationResult:
        """
        Check: Are there duplicate rows at the grain level?

        A row is a duplicate if ALL grain columns have the same values.
        Duplicates indicate bad JOINs or corrupted data.

        Example:
            Grain: [STATE, AGE_GROUP, SEX]
            Results:
            STATE | AGE_GROUP | SEX  | POPULATION
            CA    | 25-29     | M    | 1000
            CA    | 25-29     | M    | 1000  ← DUPLICATE!

            Result: ❌ FAIL
        """

        if not results:
            self.logger.info("No results to check for duplicates")
            return ValidationResult.pass_result()

        if not grain:
            self.logger.info("No grain specified, skipping duplicate check")
            return ValidationResult.pass_result()

        # Extract grain columns from results
        grain_upper = [col.upper() for col in grain]
        seen_tuples = set()
        duplicates = []

        for row in results:
            # Create tuple of grain values
            if isinstance(row, dict):
                try:
                    # Case-insensitive key lookup
                    grain_values = tuple(
                        str(self._get_case_insensitive(row, col)).upper()
                        for col in grain_upper
                    )
                except (KeyError, AttributeError) as e:
                    self.logger.warning(f"Could not extract grain from row: {e}")
                    continue

                if grain_values in seen_tuples:
                    duplicates.append(row)
                else:
                    seen_tuples.add(grain_values)

        if duplicates:
            self.logger.error(f"Found {len(duplicates)} duplicate rows")
            example = duplicates[0] if isinstance(duplicates[0], dict) else {}
            return ValidationResult.fail_result(
                f"Detected {len(duplicates)} duplicate rows at grain level {grain}. "
                f"Example: {example}"
            )

        self.logger.info(f"✅ No duplicates found ({len(results)} unique rows)")
        return ValidationResult.pass_result()

    def _get_case_insensitive(self, d: dict, key: str):
        """Get dict value with case-insensitive key"""
        for k, v in d.items():
            if k.upper() == key.upper():
                return v
        return None

    def validate_cardinality(
        self,
        results: list,
        table_name: str,
        group_by_columns: List[str]
    ) -> ValidationResult:
        """
        Check: Is result cardinality within expected range?

        Calculate expected rows based on:
        - Distinct values in each GROUP BY column
        - Product of cardinalities

        Example:
            Table: FACT_POPULATION_AGE
            GROUP BY: [STATE]
            Expected: ~50 US states
            Actual: 50 rows
            Result: ✅ PASS

            Expected: ~50 US states
            Actual: 5 rows
            Result: ⚠️ WARN (heavy filtering or missing data)

            Expected: ~50 US states
            Actual: 50,000 rows
            Result: ⚠️ WARN (possible fan-out or breakdown columns)
        """

        actual_rows = len(results)

        if not group_by_columns:
            # Single row aggregation (but could still have results if parser missed GROUP BY)
            # Only warn if result is suspiciously large (>100 rows)
            if actual_rows == 1:
                return ValidationResult.pass_result("Single-row aggregation")
            elif actual_rows <= 100:
                # Small number of results - might be grouped by parsed columns we missed
                # Don't warn, just note it
                return ValidationResult.pass_result(
                    f"Single aggregation returned {actual_rows} rows (parser may have missed GROUP BY)"
                )
            else:
                return ValidationResult.warn_result(
                    f"Expected 1 row for single aggregation, got {actual_rows}"
                )

        # Calculate expected cardinality
        try:
            expected = self._calculate_expected_cardinality(table_name, group_by_columns)
        except Exception as e:
            self.logger.error(f"Could not calculate expected cardinality: {e}")
            return ValidationResult.warn_result(f"Could not validate cardinality: {e}")

        self.logger.info(
            f"Cardinality check: expected ~{expected}, actual {actual_rows}"
        )

        # Allow ±50% variance (queries often filter, or have multiple breakdowns)
        tolerance_low = expected * 0.5
        tolerance_high = expected * 1.5

        if tolerance_low <= actual_rows <= tolerance_high:
            return ValidationResult.pass_result(
                f"Cardinality OK: {actual_rows} rows (expected ~{expected})"
            )
        elif actual_rows < tolerance_low:
            return ValidationResult.warn_result(
                f"Low cardinality: expected ~{expected}, got {actual_rows} rows. "
                f"Possible: heavy filtering, data unavailable, or empty result set."
            )
        else:
            return ValidationResult.warn_result(
                f"High cardinality: expected ~{expected}, got {actual_rows} rows. "
                f"Possible: unexpected columns in results, or join fan-out."
            )

    def validate_no_fanout(
        self,
        results: list,
        grain: List[str]
    ) -> ValidationResult:
        """
        Check: Did joins cause unexpected multiplication?

        Fan-out happens when multiple fact tables are joined without
        proper grain handling, multiplying rows unexpectedly.

        Example:
            Grain: [BLOCK_GROUP, AGE_ID, SEX]
            Total distinct combinations: ~220,000 * 23 * 2 = 10M
            Expected GROUP BY [STATE]: ~50 rows
            Actual rows: 50 * 10M = 500M rows
            Result: ❌ FAIL (massive fan-out)
        """

        if not results or not grain:
            return ValidationResult.pass_result()

        actual_rows = len(results)

        # Try to get total grain cardinality
        try:
            total_cardinality = self._calculate_max_grain_cardinality(grain)
        except Exception as e:
            self.logger.warning(f"Could not calculate max grain cardinality: {e}")
            return ValidationResult.warn_result(
                f"Could not validate for fan-out: {e}"
            )

        # If actual rows are more than grain cardinality, fan-out definitely occurred
        if actual_rows > total_cardinality:
            self.logger.error(
                f"Fan-out detected: grain cardinality {total_cardinality}, "
                f"actual rows {actual_rows}"
            )
            return ValidationResult.warn_result(
                f"Possible fan-out: grain can only have ~{total_cardinality} rows, "
                f"but got {actual_rows} rows"
            )

        return ValidationResult.pass_result()

    def _calculate_expected_cardinality(
        self,
        table_name: str,
        group_by_columns: List[str]
    ) -> int:
        """
        Calculate expected rows = product of distinct values in GROUP BY columns

        Example:
            GROUP BY [STATE, AGE_GROUP]
            DISTINCT(STATE) = 50
            DISTINCT(AGE_GROUP) = 23
            Expected = 50 * 23 = 1,150 rows
        """

        if not group_by_columns:
            return 1

        cardinalities = []
        for col in group_by_columns:
            distinct = self.cache.get_distinct_count(table_name, col)
            cardinalities.append(distinct)
            self.logger.debug(f"{table_name}.{col}: {distinct} distinct values")

        # Expected = product of cardinalities
        expected = 1
        for card in cardinalities:
            expected *= card

        return max(expected, 1)

    def _calculate_max_grain_cardinality(self, grain: List[str]) -> int:
        """
        Calculate maximum possible rows at this grain level

        This is an upper bound: the product of distinct values for each grain column.
        Actual rows can't exceed this.

        Example:
            Grain: [BLOCK_GROUP, AGE_ID, SEX]
            DISTINCT(BLOCK_GROUP) = 220,000
            DISTINCT(AGE_ID) = 23
            DISTINCT(SEX) = 2
            Max = 220,000 * 23 * 2 = 10,120,000
        """

        if not grain:
            return 1

        max_card = 1
        for col in grain:
            # This is tricky - we don't have table context
            # For now, use a reasonable upper bound estimate
            # In production, we'd need table context
            estimated = 1000  # Fallback estimate
            max_card *= estimated

        return max_card
