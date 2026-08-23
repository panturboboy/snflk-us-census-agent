# Deploy to Streamlit in Snowflake

Streamlit in Snowflake allows you to run Streamlit apps natively on Snowflake infrastructure without external hosting.

## Prerequisites

- Snowflake account (Enterprise edition or higher for some features)
- Cortex AI enabled
- Semantic view deployed: `CENSUS_DEMOGRAPHICS_MODEL`
- Appropriate warehouse for compute

## Deployment Steps

### 1. Create Storage Stage

```sql
-- As ACCOUNTADMIN or role with CREATE STAGE privilege
CREATE OR REPLACE STAGE streamlit_code_stage
DIRECTORY = (ENABLE = TRUE)
COMMENT = 'Stage for Streamlit app code';
```

### 2. Upload Application Files

```bash
# Navigate to project directory
cd /Users/Iaroslav/Projects/Snowflake/CensusAgent

# Upload main app
PUT streamlit_app.py @streamlit_code_stage;

# Upload requirements
PUT requirements.txt @streamlit_code_stage;

# Upload src directory
PUT src/config.py @streamlit_code_stage/src/;
PUT src/cortex_analyst.py @streamlit_code_stage/src/;
PUT src/__init__.py @streamlit_code_stage/src/;
```

Or use Snowflake console to upload files.

### 3. Create Streamlit App

```sql
-- Create the Streamlit app
CREATE OR REPLACE STREAMLIT CENSUS_DEMOGRAPHICS_CHAT
  ROOT_LOCATION = @streamlit_code_stage
  MAIN_FILE = '/streamlit_app.py'
  QUERY_WAREHOUSE = YOUR_WAREHOUSE  -- e.g., COMPUTE_WH
  COMMENT = 'Interactive Census Demographics Chat Interface';
```

### 4. Launch App

**Via Snowflake Console:**
1. Navigate to **Streamlit** → **Streamlit apps**
2. Click on `CENSUS_DEMOGRAPHICS_CHAT`
3. App will load and be accessible via URL

**Via SQL:**
```sql
SELECT * FROM INFORMATION_SCHEMA.STREAMLITS WHERE NAME = 'CENSUS_DEMOGRAPHICS_CHAT';
```

The app is now accessible to users with appropriate permissions.

## Access Control

### Grant Permissions to Users

```sql
-- Allow specific role to use the app
GRANT USE_STREAMLIT ON STREAMLIT CENSUS_DEMOGRAPHICS_CHAT TO ROLE analyst_role;

-- Or grant to account-wide
GRANT USE_STREAMLIT ON ALL STREAMLITS IN SCHEMA PUBLIC TO ROLE analyst_role;
```

## Updating the App

When you update `streamlit_app.py` or dependencies:

1. **Upload new files**:
   ```bash
   PUT streamlit_app.py @streamlit_code_stage OVERWRITE;
   ```

2. **Restart app**: Click "Restart" in Snowflake console

3. Changes take effect immediately

## Environment & Configuration

The app uses Streamlit's native `st.connection("snowflake")` which automatically:
- Uses current Snowflake session credentials
- Accesses the active database/schema
- Respects warehouse settings

No `.env` file needed in Streamlit in Snowflake!

## Monitoring & Logs

View app usage and logs:

```sql
-- Check app execution history
SELECT * 
FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY 
WHERE QUERY_TEXT ILIKE '%STREAMLIT%'
ORDER BY START_TIME DESC;

-- Monitor Cortex API usage
SELECT * 
FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_USAGE
ORDER BY START_TIME DESC;
```

## Troubleshooting

### App Not Loading
- Verify semantic view exists: 
  ```sql
  SELECT * FROM INFORMATION_SCHEMA.VIEWS 
  WHERE TABLE_NAME = 'CENSUS_DEMOGRAPHICS_MODEL';
  ```
- Check warehouse is running
- Verify role has `USE_CORTEX` privilege

### Cortex Queries Failing
- Verify Cortex is enabled:
  ```sql
  SELECT SYSTEM$CORTEX_ENABLED();
  ```
- Check role permissions:
  ```sql
  SHOW GRANTS ON ACCOUNT;
  ```

### Slow Performance
- Scale up warehouse: `ALTER WAREHOUSE warehouse_name SET WAREHOUSE_SIZE = 'LARGE'`
- Check query history for slow Cortex calls

## Scaling

### Multiple Environments

```sql
-- Development
CREATE OR REPLACE STREAMLIT census_chat_dev
  ROOT_LOCATION = @streamlit_code_stage_dev
  MAIN_FILE = '/streamlit_app.py'
  QUERY_WAREHOUSE = dev_wh;

-- Production
CREATE OR REPLACE STREAMLIT census_chat_prod
  ROOT_LOCATION = @streamlit_code_stage_prod
  MAIN_FILE = '/streamlit_app.py'
  QUERY_WAREHOUSE = prod_wh;
```

## Limitations

- Max execution time: 60 seconds per query
- Conversation context limited to last 5 messages
- Requires active Snowflake session (no anonymous access)

## Cost Optimization

1. Use smaller warehouse for light usage
2. Implement query caching in Cortex
3. Monitor Cortex API costs: `SNOWFLAKE.CORTEX.*` charges apply
4. Set warehouse auto-suspend to 5-10 minutes
