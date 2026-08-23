"""Orchestrate all validation checks"""

import logging
from typing import Optional
from dataclasses import dataclass, field
from src.validation.schema_cache import SemanticMetadataCache
from src.validation.query_parser import QueryParser
from src.validation.grain_validator import GrainValidator, ValidationResult
from src.validation.result_validator import ResultValidator

logger = logging.getLogger(__name__)


@dataclass
class ValidationReport:
    """Overall validation result"""
    status: str  # 'PASS', 'WARN', 'FAIL'
    message: str = ""
    checks: dict = field(default_factory=dict)

    def add_check(self, name: str, result: ValidationResult):
        """Add a validation check result"""
        self.checks[name] = {
            'status': result.status,
            'message': result.message,
            'details': result.details
        }

    def aggregate_status(self):
        """Determine overall status from all checks"""
        # FAIL if any check failed
        has_fail = any(c['status'] == 'FAIL' for c in self.checks.values())
        if has_fail:
            self.status = 'FAIL'
            return

        # WARN if any check warned
        has_warn = any(c['status'] == 'WARN' for c in self.checks.values())
        if has_warn:
            self.status = 'WARN'
            return

        # Otherwise PASS
        self.status = 'PASS'


class QueryValidator:
    """
    Orchestrate all validation checks

    Runs 4-check validation:
    1. Grain Validation (query GROUP BY matches fact table grain)
    2. Duplicate Validation (no duplicate rows at grain level)
    3. Fan-out Validation (joins didn't multiply unexpectedly)
    4. Cardinality Validation (result row counts are reasonable)
    """

    def __init__(self, metadata_cache: Optional[SemanticMetadataCache] = None):
        self.metadata_cache = metadata_cache or SemanticMetadataCache(refresh_minutes=60)
        self.grain_validator = GrainValidator(self.metadata_cache)
        self.result_validator = ResultValidator(self.metadata_cache)
        self.query_parser = QueryParser()
        self.logger = logger

    def validate_compiled_query(self, sql: str) -> ValidationReport:
        """
        Validate a compiled SQL query

        Returns ValidationReport with status 'PASS' / 'WARN' / 'FAIL'
        """

        self.logger.info(f"Validating query (first 200 chars): {sql[:200]}...")

        report = ValidationReport(status='PASS')

        try:
            # Parse query
            parsed = self.query_parser.parse(sql)
            self.logger.debug(f"Parsed query: tables={parsed.tables_accessed}, "
                             f"group_by={parsed.group_by_columns}")

            # Run grain validation
            grain_result = self.grain_validator.validate(parsed)
            report.add_check('grain', grain_result)
            self.logger.info(f"Grain validation: {grain_result.status}")

        except Exception as e:
            self.logger.error(f"Grain validation error: {e}")
            report.add_check('grain', ValidationResult.fail_result(f"Validation error: {e}"))

        # Aggregate status
        report.aggregate_status()

        return report

    def validate_compiled_query_and_results(
        self,
        sql: str,
        results: list
    ) -> ValidationReport:
        """
        Validate both compiled query AND results

        Runs all 4 checks: grain, duplicates, fan-out, cardinality
        """

        self.logger.info(f"Validating query and {len(results)} results")

        report = ValidationReport(status='PASS')

        try:
            # Parse query
            parsed = self.query_parser.parse(sql)

            # 1. Grain validation
            grain_result = self.grain_validator.validate(parsed)
            report.add_check('grain', grain_result)

            # If grain failed, stop here - no point validating results
            if grain_result.status == 'FAIL':
                self.logger.warning("Grain validation failed, stopping validation")
                report.aggregate_status()
                return report

            # Get grain from cache for result validation
            grain = []
            for table in parsed.tables_accessed:
                if not table.startswith('DIM_'):
                    grain = self.metadata_cache.get_grain(table)
                    if grain:
                        break

            # 2. Duplicate validation
            dup_result = self.result_validator.validate_no_duplicates(results, grain)
            report.add_check('duplicates', dup_result)

            # 3. Fan-out validation
            fanout_result = self.result_validator.validate_no_fanout(results, grain)
            report.add_check('fanout', fanout_result)

            # 4. Cardinality validation
            if parsed.tables_accessed:
                table = parsed.tables_accessed[0]
                card_result = self.result_validator.validate_cardinality(
                    results, table, parsed.group_by_columns or []
                )
                report.add_check('cardinality', card_result)

        except Exception as e:
            self.logger.error(f"Validation error: {e}", exc_info=True)
            report.add_check('error', ValidationResult.fail_result(f"Validation error: {e}"))

        # Aggregate status
        report.aggregate_status()

        self.logger.info(f"Validation complete: {report.status}")
        for check_name, check_result in report.checks.items():
            self.logger.info(f"  {check_name}: {check_result['status']}")

        return report
