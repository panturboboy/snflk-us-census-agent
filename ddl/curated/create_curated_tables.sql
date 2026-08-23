-- ============================================================================
-- CURATED LAYER: Cleaned, Deduplicated, Standardized Census Data
-- ============================================================================
-- These tables are your 3 curated demographic tables.
-- Applied transformations: deduplication, null handling, standardization.

-- Get the exact DDLs by running in Snowflake:
-- SELECT GET_DDL('TABLE', 'SCHEMA_NAME.TABLE_NAME');

-- Then paste your CREATE TABLE statements below:

-- ============================================================================
-- TABLE 1: Population by Age and Sex (Block Group Level)
-- ============================================================================
-- Curated demographics data with age and sex breakdowns at block group granularity.
-- Source: US Census American Community Survey via Snowflake Marketplace

CREATE OR REPLACE TABLE FACT_POPULATION_AGE (
    CENSUS_BLOCK_GROUP VARCHAR(16777216) COMMENT 'Census block group identifier',
    AGE_ID NUMBER(2,0) COMMENT 'Numeric age group identifier',
    AGE_CODE VARCHAR(8) COMMENT 'Age code from Census Bureau',
    SEX VARCHAR(6) COMMENT 'Sex category (Male, Female, or Total)',
    ESTIMATE FLOAT COMMENT 'Population estimate from ACS',
    MARGIN_OF_ERROR FLOAT COMMENT 'Margin of error for estimate'
);


-- ============================================================================
-- TABLE 2: Age Groups Dimension (Reference Data)
-- ============================================================================
-- Standardized age group mappings from Census Bureau age codes.
-- Provides human-readable labels and age ranges for analysis.

CREATE OR REPLACE VIEW DIM_AGE (
    AGE_ID,
    AGE_CODE,
    AGE_LABEL,
    AGE_MIN,
    AGE_MAX
) AS
SELECT
    1 AS AGE_ID,
    'UNDER_5' AS AGE_CODE,
    'Under 5 years' AS AGE_LABEL,
    0 AS AGE_MIN,
    4 AS AGE_MAX

UNION ALL
SELECT 2, '5_TO_9', '5 to 9 years', 5, 9
UNION ALL
SELECT 3, '10_TO_14', '10 to 14 years', 10, 14
UNION ALL
SELECT 4, '15_TO_17', '15 to 17 years', 15, 17
UNION ALL
SELECT 5, '18_TO_19', '18 to 19 years', 18, 19
UNION ALL
SELECT 6, '20', '20 years', 20, 20
UNION ALL
SELECT 7, '21', '21 years', 21, 21
UNION ALL
SELECT 8, '22_TO_24', '22 to 24 years', 22, 24
UNION ALL
SELECT 9, '25_TO_29', '25 to 29 years', 25, 29
UNION ALL
SELECT 10, '30_TO_34', '30 to 34 years', 30, 34
UNION ALL
SELECT 11, '35_TO_39', '35 to 39 years', 35, 39
UNION ALL
SELECT 12, '40_TO_44', '40 to 44 years', 40, 44
UNION ALL
SELECT 13, '45_TO_49', '45 to 49 years', 45, 49
UNION ALL
SELECT 14, '50_TO_54', '50 to 54 years', 50, 54
UNION ALL
SELECT 15, '55_TO_59', '55 to 59 years', 55, 59
UNION ALL
SELECT 16, '60_TO_61', '60 to 61 years', 60, 61
UNION ALL
SELECT 17, '62_TO_64', '62 to 64 years', 62, 64
UNION ALL
SELECT 18, '65_TO_66', '65 to 66 years', 65, 66
UNION ALL
SELECT 19, '67_TO_69', '67 to 69 years', 67, 69
UNION ALL
SELECT 20, '70_TO_74', '70 to 74 years', 70, 74
UNION ALL
SELECT 21, '75_TO_79', '75 to 79 years', 75, 79
UNION ALL
SELECT 22, '80_TO_84', '80 to 84 years', 80, 84
UNION ALL
SELECT 23, '85_PLUS', '85 years and over', 85, NULL;


-- ============================================================================
-- TABLE 3: Block Group Geography Dimension (Reference Data)
-- ============================================================================
-- Census block group geographic hierarchy with spatial geometry.
-- Source: Snowflake Marketplace US Census dataset

CREATE OR REPLACE VIEW DIM_BLOCK_GROUP (
    BLOCK_GROUP_KEY,
    STATE_FIPS,
    COUNTY_FIPS,
    TRACT_CODE,
    BLOCK_GROUP,
    STATE_CODE,
    STATE_NAME,
    STATE_NAME_FULL,
    COUNTY_NAME,
    MTFCC,
    GEOMETRY
) AS
SELECT
    CENSUS_BLOCK_GROUP                         AS BLOCK_GROUP_KEY,
    STATE_FIPS                                 AS STATE_FIPS,
    COUNTY_FIPS                                AS COUNTY_FIPS,
    TRACT_CODE                                 AS TRACT_CODE,
    CENSUS_BLOCK_GROUP                         AS BLOCK_GROUP,
    STATE                                      AS STATE_CODE,
    STATE                                      AS STATE_NAME,
    CASE STATE
        WHEN 'AL' THEN 'Alabama'
        WHEN 'AK' THEN 'Alaska'
        WHEN 'AZ' THEN 'Arizona'
        WHEN 'AR' THEN 'Arkansas'
        WHEN 'CA' THEN 'California'
        WHEN 'CO' THEN 'Colorado'
        WHEN 'CT' THEN 'Connecticut'
        WHEN 'DE' THEN 'Delaware'
        WHEN 'FL' THEN 'Florida'
        WHEN 'GA' THEN 'Georgia'
        WHEN 'HI' THEN 'Hawaii'
        WHEN 'ID' THEN 'Idaho'
        WHEN 'IL' THEN 'Illinois'
        WHEN 'IN' THEN 'Indiana'
        WHEN 'IA' THEN 'Iowa'
        WHEN 'KS' THEN 'Kansas'
        WHEN 'KY' THEN 'Kentucky'
        WHEN 'LA' THEN 'Louisiana'
        WHEN 'ME' THEN 'Maine'
        WHEN 'MD' THEN 'Maryland'
        WHEN 'MA' THEN 'Massachusetts'
        WHEN 'MI' THEN 'Michigan'
        WHEN 'MN' THEN 'Minnesota'
        WHEN 'MS' THEN 'Mississippi'
        WHEN 'MO' THEN 'Missouri'
        WHEN 'MT' THEN 'Montana'
        WHEN 'NE' THEN 'Nebraska'
        WHEN 'NV' THEN 'Nevada'
        WHEN 'NH' THEN 'New Hampshire'
        WHEN 'NJ' THEN 'New Jersey'
        WHEN 'NM' THEN 'New Mexico'
        WHEN 'NY' THEN 'New York'
        WHEN 'NC' THEN 'North Carolina'
        WHEN 'ND' THEN 'North Dakota'
        WHEN 'OH' THEN 'Ohio'
        WHEN 'OK' THEN 'Oklahoma'
        WHEN 'OR' THEN 'Oregon'
        WHEN 'PA' THEN 'Pennsylvania'
        WHEN 'RI' THEN 'Rhode Island'
        WHEN 'SC' THEN 'South Carolina'
        WHEN 'SD' THEN 'South Dakota'
        WHEN 'TN' THEN 'Tennessee'
        WHEN 'TX' THEN 'Texas'
        WHEN 'UT' THEN 'Utah'
        WHEN 'VT' THEN 'Vermont'
        WHEN 'VA' THEN 'Virginia'
        WHEN 'WA' THEN 'Washington'
        WHEN 'WV' THEN 'West Virginia'
        WHEN 'WI' THEN 'Wisconsin'
        WHEN 'WY' THEN 'Wyoming'
        WHEN 'DC' THEN 'District of Columbia'
        ELSE STATE
    END                                       AS STATE_NAME_FULL,
    COUNTY                                     AS COUNTY_NAME,
    MTFCC                                      AS MTFCC,
    TRY_TO_GEOGRAPHY(GEOMETRY)                 AS GEOMETRY
FROM
    US_OPEN_CENSUS_DATA_NEIGHBORHOOD_INSIGHTS_FREE_DATASET.PUBLIC."2020_CBG_GEOMETRY_WKT";


-- ============================================================================
-- TABLE 4: Race and Ethnicity by Block Group (Fact Table)
-- ============================================================================
-- Racial and ethnic composition from Census Bureau race/ethnicity categories (ACS B02001).
-- Provides detailed demographic breakdown for socioeconomic analysis.

CREATE OR REPLACE TABLE FACT_RACE_ETHNICITY (
    CENSUS_BLOCK_GROUP VARCHAR(16777216) COMMENT 'Census block group identifier',
    RACE_ID NUMBER(2,0) COMMENT 'Numeric race/ethnicity category identifier',
    RACE_CODE VARCHAR(16) COMMENT 'Race/ethnicity code from Census Bureau',
    ESTIMATE FLOAT COMMENT 'Population estimate for race/ethnicity category',
    MARGIN_OF_ERROR FLOAT COMMENT 'Margin of error for estimate'
);


-- ============================================================================
-- TABLE 5: Race and Ethnicity Dimension (Reference Data)
-- ============================================================================
-- Standard Census Bureau race and ethnicity categories from ACS B02001.
-- Provides human-readable labels for all racial/ethnic classifications.

CREATE OR REPLACE VIEW DIM_RACE (
    RACE_ID,
    RACE_CODE,
    RACE_LABEL,
    RACE_CATEGORY
) AS
SELECT
    1 AS RACE_ID,
    'TOTAL' AS RACE_CODE,
    'Total Population' AS RACE_LABEL,
    'Total' AS RACE_CATEGORY

UNION ALL
SELECT 2, 'WHITE_ALONE', 'White Alone', 'White'
UNION ALL
SELECT 3, 'BLACK_ALONE', 'Black or African American Alone', 'Black'
UNION ALL
SELECT 4, 'AMERICAN_INDIAN_ALASKA_NATIVE_ALONE', 'American Indian and Alaska Native Alone', 'Native'
UNION ALL
SELECT 5, 'ASIAN_ALONE', 'Asian Alone', 'Asian'
UNION ALL
SELECT 6, 'NATIVE_HAWAIIAN_PACIFIC_ISLANDER_ALONE', 'Native Hawaiian and Other Pacific Islander Alone', 'Pacific Islander'
UNION ALL
SELECT 7, 'SOME_OTHER_RACE_ALONE', 'Some Other Race Alone', 'Other'
UNION ALL
SELECT 8, 'TWO_OR_MORE_RACES', 'Two or More Races', 'Mixed'
UNION ALL
SELECT 9, 'HISPANIC_LATINO_ANY_RACE', 'Hispanic or Latino (any race)', 'Hispanic/Latino';


-- ============================================================================
-- TABLE 6: Household Composition by Block Group (Fact Table)
-- ============================================================================
-- Household types and family composition from Census Bureau (ACS B11001).
-- Distinguishes family vs. non-family households for housing analysis.

CREATE OR REPLACE TABLE FACT_HOUSEHOLD_COMPOSITION (
    CENSUS_BLOCK_GROUP VARCHAR(16777216) COMMENT 'Census block group identifier',
    HOUSEHOLD_TYPE_ID NUMBER(2,0) COMMENT 'Numeric household type identifier',
    HOUSEHOLD_TYPE_CODE VARCHAR(32) COMMENT 'Household type code from Census Bureau',
    ESTIMATE FLOAT COMMENT 'Number of households of this type',
    MARGIN_OF_ERROR FLOAT COMMENT 'Margin of error for estimate'
);


-- ============================================================================
-- TABLE 7: Household Type Dimension (Reference Data)
-- ============================================================================
-- Standardized household classification from ACS B11001.
-- Defines family, non-family, and related household categories.

CREATE OR REPLACE VIEW DIM_HOUSEHOLD_TYPE (
    HOUSEHOLD_TYPE_ID,
    HOUSEHOLD_TYPE_CODE,
    HOUSEHOLD_TYPE_LABEL,
    HOUSEHOLD_CATEGORY
) AS
SELECT
    1 AS HOUSEHOLD_TYPE_ID,
    'TOTAL_HOUSEHOLDS' AS HOUSEHOLD_TYPE_CODE,
    'Total Households' AS HOUSEHOLD_TYPE_LABEL,
    'Total' AS HOUSEHOLD_CATEGORY

UNION ALL
SELECT 2, 'FAMILY_HOUSEHOLDS', 'Family Households', 'Family'
UNION ALL
SELECT 3, 'FAMILY_MARRIED_COUPLE', 'Family Households - Married Couple', 'Family'
UNION ALL
SELECT 4, 'FAMILY_MALE_HOUSEHOLDER', 'Family Households - Male Householder, No Wife', 'Family'
UNION ALL
SELECT 5, 'FAMILY_FEMALE_HOUSEHOLDER', 'Family Households - Female Householder, No Husband', 'Family'
UNION ALL
SELECT 6, 'NONFAMILY_HOUSEHOLDS', 'Non-Family Households', 'Non-Family'
UNION ALL
SELECT 7, 'NONFAMILY_ALONE', 'Non-Family Households - Living Alone', 'Non-Family'
UNION ALL
SELECT 8, 'NONFAMILY_NOT_ALONE', 'Non-Family Households - Not Living Alone', 'Non-Family';
