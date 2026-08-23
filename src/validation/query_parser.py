"""Parse SQL to extract structure for validation"""

import logging
import re
from typing import List, Dict
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class QueryStructure:
    """Parsed SQL structure"""
    tables_accessed: List[str]
    columns_selected: List[str]
    group_by_columns: List[str]
    aggregation_functions: List[str]
    where_clause: str = None


class QueryParser:
    """Extract structure from compiled SQL"""

    @staticmethod
    def parse(sql: str) -> QueryStructure:
        """
        Parse SQL query to extract structure

        Returns QueryStructure with tables, columns, GROUP BY, aggregations
        """
        sql_upper = sql.upper()

        # Extract FROM clause tables
        tables = QueryParser._extract_tables(sql)
        logger.debug(f"Tables in query: {tables}")

        # Extract SELECT columns
        columns = QueryParser._extract_select_columns(sql)
        logger.debug(f"Columns selected: {columns}")

        # Extract GROUP BY columns
        group_by = QueryParser._extract_group_by(sql)
        logger.debug(f"GROUP BY columns: {group_by}")

        # Extract aggregation functions
        agg_funcs = QueryParser._extract_aggregations(sql)
        logger.debug(f"Aggregations: {agg_funcs}")

        # Extract WHERE clause
        where = QueryParser._extract_where(sql)

        return QueryStructure(
            tables_accessed=tables,
            columns_selected=columns,
            group_by_columns=group_by,
            aggregation_functions=agg_funcs,
            where_clause=where
        )

    @staticmethod
    def _extract_tables(sql: str) -> List[str]:
        """Extract table names from FROM and JOIN clauses"""
        # Find FROM table (handles SCHEMA.TABLE format)
        from_pattern = r'FROM\s+(?:\w+\.)?(\w+)'
        from_matches = re.findall(from_pattern, sql, re.IGNORECASE)

        # Find JOIN tables (handles SCHEMA.TABLE format)
        join_pattern = r'JOIN\s+(?:\w+\.)?(\w+)'
        join_matches = re.findall(join_pattern, sql, re.IGNORECASE)

        tables = []
        for match in from_matches + join_matches:
            table_name = match.upper()
            if table_name not in tables:
                tables.append(table_name)

        return tables

    @staticmethod
    def _extract_select_columns(sql: str) -> List[str]:
        """Extract columns from SELECT clause"""
        # Find SELECT...FROM region
        select_pattern = r'SELECT\s+(.*?)\s+FROM'
        match = re.search(select_pattern, sql, re.IGNORECASE | re.DOTALL)

        if not match:
            return []

        select_part = match.group(1)
        columns = [col.strip() for col in select_part.split(',')]

        return columns

    @staticmethod
    def _extract_group_by(sql: str) -> List[str]:
        """Extract GROUP BY columns"""
        pattern = r'GROUP\s+BY\s+(.*?)(?:HAVING|ORDER|$)'
        match = re.search(pattern, sql, re.IGNORECASE | re.DOTALL)

        if not match:
            return []

        group_by_part = match.group(1).strip()
        columns = [col.strip().upper() for col in group_by_part.split(',')]

        # Clean up column names (remove table aliases)
        cleaned = []
        for col in columns:
            # Handle "TABLE.COLUMN" format
            if '.' in col:
                col = col.split('.')[-1]
            cleaned.append(col)

        return cleaned

    @staticmethod
    def _extract_aggregations(sql: str) -> List[str]:
        """Extract aggregation functions"""
        agg_pattern = r'(SUM|AVG|COUNT|MAX|MIN|STDDEV|VARIANCE)\s*\('
        matches = re.findall(agg_pattern, sql, re.IGNORECASE)
        return [m.upper() for m in matches]

    @staticmethod
    def _extract_where(sql: str) -> str:
        """Extract WHERE clause"""
        pattern = r'WHERE\s+(.*?)(?:GROUP|ORDER|HAVING|$)'
        match = re.search(pattern, sql, re.IGNORECASE | re.DOTALL)

        if match:
            return match.group(1).strip()
        return None
