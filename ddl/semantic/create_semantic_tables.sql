-- ============================================================================
-- SNOWFLAKE SEMANTIC VIEW: Census Demographics
-- ============================================================================
-- Business-friendly semantic model for Cortex Analyst to understand demographics data.
-- Defines relationships, dimensions, and metrics for Census analysis.

CREATE OR REPLACE SEMANTIC VIEW CENSUS_DEMOGRAPHICS_MODEL

TABLES (
  population_age AS CURATED.FACT_POPULATION_AGE
    PRIMARY KEY (AGE_ID, SEX, CENSUS_BLOCK_GROUP),

  race_ethnicity AS CURATED.FACT_RACE_ETHNICITY
    PRIMARY KEY (RACE_ID, CENSUS_BLOCK_GROUP),

  household_composition AS CURATED.FACT_HOUSEHOLD_COMPOSITION
    PRIMARY KEY (HOUSEHOLD_TYPE_ID, CENSUS_BLOCK_GROUP),

  age AS CURATED.DIM_AGE
    PRIMARY KEY (AGE_ID),

  race AS CURATED.DIM_RACE
    PRIMARY KEY (RACE_ID),

  household_type AS CURATED.DIM_HOUSEHOLD_TYPE
    PRIMARY KEY (HOUSEHOLD_TYPE_ID),

  block_group AS CURATED.DIM_BLOCK_GROUP
    PRIMARY KEY (BLOCK_GROUP)
)

RELATIONSHIPS (
  population_to_age AS
    population_age (AGE_ID)
    REFERENCES age (AGE_ID),

  population_to_block_group AS
    population_age (CENSUS_BLOCK_GROUP)
    REFERENCES block_group (BLOCK_GROUP),

  race_to_race_category AS
    race_ethnicity (RACE_ID)
    REFERENCES race (RACE_ID),

  race_to_block_group AS
    race_ethnicity (CENSUS_BLOCK_GROUP)
    REFERENCES block_group (BLOCK_GROUP),

  household_to_household_type AS
    household_composition (HOUSEHOLD_TYPE_ID)
    REFERENCES household_type (HOUSEHOLD_TYPE_ID),

  household_to_block_group AS
    household_composition (CENSUS_BLOCK_GROUP)
    REFERENCES block_group (BLOCK_GROUP)
)

DIMENSIONS (
  block_group.state_fips
    AS block_group.STATE_FIPS
    COMMENT = 'Federal Information Processing Standards code for state',

  block_group.state_name
    AS block_group.STATE_NAME_FULL
    COMMENT = 'Full name of the US state or territory',

  block_group.county_fips
    AS block_group.COUNTY_FIPS
    COMMENT = 'FIPS code for county within state',

  block_group.county_name
    AS block_group.COUNTY_NAME
    COMMENT = 'Full name of the county',

  block_group.block_group_key
    AS block_group.BLOCK_GROUP_KEY
    COMMENT = 'Unique Census block group identifier',

  age.age_id
    AS age.AGE_ID
    COMMENT = 'Numeric ID for age group',

  age.age_label
    AS age.AGE_LABEL
    COMMENT = 'Human-readable age group label',

  age.age_min
    AS age.AGE_MIN
    COMMENT = 'Minimum age in the age group',

  age.age_max
    AS age.AGE_MAX
    COMMENT = 'Maximum age in the age group',

  population_age.sex
    AS population_age.SEX
    COMMENT = 'Sex category: Male, Female, or Total',

  race.race_label
    AS race.RACE_LABEL
    COMMENT = 'Human-readable race/ethnicity category',

  race.race_category
    AS race.RACE_CATEGORY
    COMMENT = 'Broad race category: White, Black, Asian, Hispanic, etc.',

  household_type.household_type_label
    AS household_type.HOUSEHOLD_TYPE_LABEL
    COMMENT = 'Human-readable household type',

  household_type.household_category
    AS household_type.HOUSEHOLD_CATEGORY
    COMMENT = 'Household category: Family or Non-Family'
)

METRICS (
  population_age.population_estimate
    AS SUM(population_age.ESTIMATE)
    WITH SYNONYMS = (
      'population',
      'headcount',
      'residents',
      'inhabitants',
      'people',
      'total'
    )
    COMMENT = 'Total population estimate from American Community Survey',

  population_age.population_average
    AS AVG(population_age.ESTIMATE)
    WITH SYNONYMS = (
      'average population',
      'mean population'
    )
    COMMENT = 'Average population per record',

  population_age.margin_of_error
    AS AVG(population_age.MARGIN_OF_ERROR)
    WITH SYNONYMS = (
      'error',
      'uncertainty',
      'confidence',
      'moe'
    )
    COMMENT = 'Average margin of error for population estimate',

  race_ethnicity.race_population_estimate
    AS SUM(race_ethnicity.ESTIMATE)
    WITH SYNONYMS = (
      'race population',
      'ethnicity population',
      'racial composition'
    )
    COMMENT = 'Total population by race/ethnicity category',

  race_ethnicity.race_population_margin_of_error
    AS AVG(race_ethnicity.MARGIN_OF_ERROR)
    WITH SYNONYMS = (
      'race error',
      'ethnicity error'
    )
    COMMENT = 'Average margin of error for race/ethnicity estimates',

  household_composition.household_estimate
    AS SUM(household_composition.ESTIMATE)
    WITH SYNONYMS = (
      'households',
      'household count',
      'family households',
      'nonfamily households'
    )
    COMMENT = 'Total number of households by type',

  household_composition.household_margin_of_error
    AS AVG(household_composition.MARGIN_OF_ERROR)
    WITH SYNONYMS = (
      'household error'
    )
    COMMENT = 'Average margin of error for household estimates'
)

COMMENT = 'Business-friendly semantic model for Census demographics analysis';
