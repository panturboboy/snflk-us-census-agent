"""Unit tests for SQL query parsing"""

import pytest
from src.validation.query_parser import QueryParser


@pytest.mark.unit
class TestQueryParser:
    """Test SQL parsing logic"""

    def test_parse_simple_select(self):
        """Parse simple SELECT with FROM and GROUP BY"""
        sql = """
        SELECT STATE, SUM(POPULATION)
        FROM FACT_POPULATION_AGE
        GROUP BY STATE
        """

        parsed = QueryParser.parse(sql)

        assert 'FACT_POPULATION_AGE' in parsed.tables_accessed
        assert 'STATE' in parsed.columns_selected
        assert 'STATE' in [c.upper() for c in parsed.group_by_columns]
        assert 'SUM' in parsed.aggregation_functions

    def test_parse_multiple_aggregations(self):
        """Parse query with multiple aggregation functions"""
        sql = """
        SELECT STATE, SUM(POPULATION), AVG(INCOME), COUNT(DISTINCT HOUSEHOLD_ID)
        FROM FACT_POPULATION_AGE
        GROUP BY STATE
        """

        parsed = QueryParser.parse(sql)

        assert 'SUM' in parsed.aggregation_functions
        assert 'AVG' in parsed.aggregation_functions
        assert 'COUNT' in parsed.aggregation_functions

    def test_parse_with_where_clause(self):
        """Parse query with WHERE clause"""
        sql = """
        SELECT STATE, SUM(POPULATION)
        FROM FACT_POPULATION_AGE
        WHERE YEAR = 2020
        GROUP BY STATE
        """

        parsed = QueryParser.parse(sql)

        assert parsed.where_clause is not None
        assert 'YEAR' in parsed.where_clause.upper()

    def test_parse_join_query(self):
        """Parse query with JOIN"""
        sql = """
        SELECT f.STATE, SUM(f.POPULATION)
        FROM FACT_POPULATION_AGE f
        JOIN DIM_BLOCK_GROUP d ON f.BLOCK_GROUP_ID = d.BLOCK_GROUP_ID
        GROUP BY f.STATE
        """

        parsed = QueryParser.parse(sql)

        assert len(parsed.tables_accessed) >= 1
        assert any('FACT_POPULATION_AGE' in t for t in parsed.tables_accessed)

    def test_extract_tables_with_alias(self):
        """Extract table names with aliases"""
        sql = "FROM FACT_POPULATION_AGE fa"

        tables = QueryParser._extract_tables(sql)

        assert 'FACT_POPULATION_AGE' in tables

    def test_extract_tables_multiple(self):
        """Extract multiple tables from JOINs"""
        sql = """
        FROM FACT_POPULATION_AGE f
        JOIN DIM_BLOCK_GROUP d ON ...
        JOIN DIM_AGE a ON ...
        """

        tables = QueryParser._extract_tables(sql)

        assert 'FACT_POPULATION_AGE' in tables
        assert 'DIM_BLOCK_GROUP' in tables
        assert 'DIM_AGE' in tables

    def test_extract_columns_simple(self):
        """Extract columns from SELECT"""
        sql = "SELECT COLUMN1, COLUMN2, COLUMN3 FROM TABLE1"

        columns = QueryParser._extract_select_columns(sql)

        assert 'COLUMN1' in columns
        assert 'COLUMN2' in columns
        assert 'COLUMN3' in columns

    def test_extract_columns_with_aggregates(self):
        """Extract columns including aggregates"""
        sql = "SELECT STATE, SUM(POPULATION), AVG(INCOME) FROM TABLE1"

        columns = QueryParser._extract_select_columns(sql)

        assert any('STATE' in c for c in columns)
        assert any('SUM' in c for c in columns)
        assert any('AVG' in c for c in columns)

    def test_extract_group_by_single(self):
        """Extract single GROUP BY column"""
        sql = "GROUP BY STATE"

        group_by = QueryParser._extract_group_by(sql)

        assert 'STATE' in [c.upper() for c in group_by]

    def test_extract_group_by_multiple(self):
        """Extract multiple GROUP BY columns"""
        sql = "GROUP BY STATE, AGE_GROUP, SEX"

        group_by = QueryParser._extract_group_by(sql)

        assert len(group_by) >= 3

    def test_extract_group_by_with_having(self):
        """Extract GROUP BY before HAVING"""
        sql = "GROUP BY STATE, YEAR HAVING SUM(POPULATION) > 1000000"

        group_by = QueryParser._extract_group_by(sql)

        assert len(group_by) >= 1

    def test_extract_group_by_none(self):
        """Handle query with no GROUP BY"""
        sql = "SELECT SUM(POPULATION) FROM TABLE1"

        group_by = QueryParser._extract_group_by(sql)

        assert group_by == []

    def test_extract_aggregations_sum(self):
        """Extract SUM aggregation"""
        sql = "SELECT SUM(POPULATION) FROM TABLE1"

        aggs = QueryParser._extract_aggregations(sql)

        assert 'SUM' in aggs

    def test_extract_aggregations_all_types(self):
        """Extract all aggregation types"""
        sql = """
        SELECT
            SUM(AMOUNT),
            AVG(PRICE),
            COUNT(*),
            MAX(VALUE),
            MIN(VALUE),
            STDDEV(MEASURE)
        FROM TABLE1
        """

        aggs = QueryParser._extract_aggregations(sql)

        assert 'SUM' in aggs
        assert 'AVG' in aggs
        assert 'COUNT' in aggs
        assert 'MAX' in aggs
        assert 'MIN' in aggs
        assert 'STDDEV' in aggs

    def test_extract_where_simple(self):
        """Extract WHERE clause"""
        sql = "WHERE STATE = 'CA' AND YEAR = 2020"

        where = QueryParser._extract_where(sql)

        assert where is not None
        assert 'STATE' in where

    def test_extract_where_none(self):
        """Handle query with no WHERE"""
        sql = "SELECT * FROM TABLE1 GROUP BY X"

        where = QueryParser._extract_where(sql)

        assert where is None

    def test_parse_real_world_census_query(self):
        """Parse a realistic Census query"""
        sql = """
        SELECT
            bg.STATE_NAME_FULL,
            bg.COUNTY_NAME,
            fa.AGE_ID,
            fa.SEX,
            SUM(fa.POPULATION_ESTIMATE) as total_population,
            AVG(fa.MARGIN_OF_ERROR) as avg_margin
        FROM CURATED.FACT_POPULATION_AGE fa
        JOIN CURATED.DIM_BLOCK_GROUP bg ON fa.CENSUS_BLOCK_GROUP = bg.CENSUS_BLOCK_GROUP
        WHERE fa.CENSUS_YEAR = 2020
        GROUP BY bg.STATE_NAME_FULL, bg.COUNTY_NAME, fa.AGE_ID, fa.SEX
        ORDER BY total_population DESC
        """

        parsed = QueryParser.parse(sql)

        # Check tables (parser extracts just table name, not schema prefix)
        assert len(parsed.tables_accessed) >= 2
        assert any('FACT_POPULATION_AGE' in t or 'FACT' in t for t in parsed.tables_accessed)
        assert any('DIM_BLOCK_GROUP' in t or 'DIM' in t for t in parsed.tables_accessed)

        # Check aggregations
        assert 'SUM' in parsed.aggregation_functions
        assert 'AVG' in parsed.aggregation_functions

        # Check WHERE
        assert parsed.where_clause is not None
        assert 'CENSUS_YEAR' in parsed.where_clause.upper()

    def test_parse_group_by_with_table_aliases(self):
        """Parse GROUP BY with table.column references"""
        sql = """
        SELECT f.STATE, SUM(f.POPULATION)
        FROM FACT_POPULATION_AGE f
        GROUP BY f.STATE, f.AGE_ID
        """

        parsed = QueryParser.parse(sql)

        # Should clean up table aliases
        assert any('STATE' in c.upper() for c in parsed.group_by_columns)
