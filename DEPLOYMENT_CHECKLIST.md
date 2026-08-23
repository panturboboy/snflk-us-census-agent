# Deployment Checklist

## Data Layer ✅

- [ ] DDL files ready in `/ddl` directory
- [ ] Curated layer deployed
  - [ ] `FACT_POPULATION_AGE` created
  - [ ] `DIM_AGE` view created
  - [ ] `DIM_BLOCK_GROUP` view created
- [ ] Semantic layer deployed
  - [ ] `CENSUS_DEMOGRAPHICS_MODEL` semantic view created

**Deployment command:**
```sql
-- Run curated layer DDL
SELECT 'Curated layer deployed' WHERE EXISTS (
  SELECT 1 FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'FACT_POPULATION_AGE'
);

-- Run semantic layer DDL
SELECT 'Semantic layer deployed' WHERE EXISTS (
  SELECT 1 FROM INFORMATION_SCHEMA.VIEWS WHERE TABLE_NAME = 'CENSUS_DEMOGRAPHICS_MODEL'
);
```

## Snowflake Configuration ✅

- [ ] Cortex AI enabled
  ```sql
  SELECT SYSTEM$CORTEX_ENABLED();
  ```

- [ ] User/role has Cortex permissions
  ```sql
  GRANT USE_CORTEX_ANALYST ON ACCOUNT TO ROLE SYSADMIN;
  GRANT USE_CORTEX ON ACCOUNT TO ROLE SYSADMIN;
  ```

- [ ] Warehouse available and running
  ```sql
  SHOW WAREHOUSES;
  ```

## Application Deployment ✅

- [ ] Create storage stage
  ```sql
  CREATE OR REPLACE STAGE streamlit_code_stage
  DIRECTORY = (ENABLE = TRUE);
  ```

- [ ] Upload files to stage
  ```bash
  # From project directory
  PUT streamlit_app.py @streamlit_code_stage;
  PUT requirements.txt @streamlit_code_stage;
  PUT src/config.py @streamlit_code_stage/src/;
  PUT src/cortex_analyst.py @streamlit_code_stage/src/;
  PUT src/__init__.py @streamlit_code_stage/src/;
  ```

- [ ] Create Streamlit app
  ```sql
  CREATE OR REPLACE STREAMLIT CENSUS_DEMOGRAPHICS_CHAT
    ROOT_LOCATION = @streamlit_code_stage
    MAIN_FILE = '/streamlit_app.py'
    QUERY_WAREHOUSE = YOUR_WAREHOUSE_NAME
    COMMENT = 'Interactive Census Demographics Chat Interface';
  ```

- [ ] Grant access to users
  ```sql
  GRANT USE_STREAMLIT ON STREAMLIT CENSUS_DEMOGRAPHICS_CHAT TO ROLE SYSADMIN;
  ```

## Testing ✅

### 1. Semantic View Query Test
```sql
SELECT SNOWFLAKE.CORTEX.ANALYST(
    'What is the population of California?',
    'CENSUS_DEMOGRAPHICS_MODEL'
) AS response;
```
✓ Should return a natural language response

### 2. Open Streamlit App
- [ ] Navigate to Streamlit apps in console
- [ ] Click `CENSUS_DEMOGRAPHICS_CHAT`
- [ ] App loads without errors

### 3. Chat Test
- [ ] Type test question: "What is the population of California?"
- [ ] ✓ Response appears within 60 seconds
- [ ] ✓ No connection errors
- [ ] ✓ Multiple follow-up questions work

### 4. Example Questions Test
- [ ] "Show population by age group"
- [ ] "Compare Texas and New York"
- [ ] "What are demographics of New York County?"

## Documentation ✅

- [ ] README.md explains architecture
- [ ] SNOWFLAKE_DEPLOYMENT.md has setup instructions
- [ ] Code comments explain key functions
- [ ] .env.example (local dev only) has all required vars

## Performance Verification ✅

- [ ] Queries complete within 60 seconds
- [ ] No timeout errors on first question
- [ ] Memory usage stable across multiple queries
- [ ] Warehouse doesn't scale unexpectedly

## Security Checklist ✅

- [ ] Only authorized roles can access app
- [ ] No hardcoded credentials in code
- [ ] SQL injection protection (string escaping)
- [ ] No sensitive data logged to console

## Issues & Rollback

If deployment fails:

1. **App won't load**
   ```sql
   ALTER STREAMLIT CENSUS_DEMOGRAPHICS_CHAT SET MAIN_FILE = '/streamlit_app.py';
   ```

2. **Connection error**
   - Verify semantic view exists
   - Check warehouse is running
   - Verify role permissions

3. **Cortex error**
   - Check Cortex is enabled: `SELECT SYSTEM$CORTEX_ENABLED();`
   - Verify role has `USE_CORTEX` grant
   - Check semantic view is correct

4. **Rollback** (if needed)
   ```sql
   DROP STREAMLIT CENSUS_DEMOGRAPHICS_CHAT;
   -- Redeploy with previous working version
   ```

## Final Sign-Off

- [ ] All data layers deployed and tested
- [ ] Streamlit app accessible and responsive
- [ ] Cortex Analyst responding correctly
- [ ] Example queries returning results
- [ ] Performance acceptable (< 60s per query)
- [ ] Documentation complete
- [ ] Ready for evaluation

**Deployment Date:** ___________
**Deployed By:** ___________
**Notes:** ___________
