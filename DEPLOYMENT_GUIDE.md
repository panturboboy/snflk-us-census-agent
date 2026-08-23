# Deployment Guide: CI/CD to Snowflake

Deploy the Census Demographics Chat app to Snowflake infrastructure via GitHub Actions.

## Prerequisites

- GitHub repository
- Snowflake account with Enterprise edition (required for Streamlit in Snowflake)
- Cortex Analyst enabled
- Semantic model deployed: `CENSUS_DEMOGRAPHICS_MODEL`

## Setup

### 1. Configure GitHub Secrets

In your GitHub repo, go to **Settings → Secrets and variables → Actions** and add:

| Secret | Value | Example |
|--------|-------|---------|
| `SNOWFLAKE_ACCOUNT` | Account identifier | `MIYVSAQ-NX19708` |
| `SNOWFLAKE_USER` | Service account username | `GITHUB_DEPLOY` |
| `SNOWFLAKE_PASSWORD` | Service account password | `<strong-password>` |
| `SNOWFLAKE_DATABASE` | Database name | `CENSUS_NEIGHBORHOOD_INSIGHTS` |
| `SNOWFLAKE_SCHEMA` | Schema name | `PUBLIC` |
| `SNOWFLAKE_WAREHOUSE` | Warehouse for app | `CENSUS_DEV_WH` |
| `CORTEX_ANALYST_TOKEN` | PAT token | (from Snowsight) |

### 2. Create Snowflake Service Account

```sql
-- As ACCOUNTADMIN
CREATE OR REPLACE USER github_deploy
  PASSWORD = '<strong-password>'
  COMMENT = 'Service account for GitHub Actions deployment';

GRANT ROLE ACCOUNTADMIN TO USER github_deploy;

-- Alternative: More restrictive role
GRANT ROLE sysadmin TO USER github_deploy;
GRANT CREATE STAGE ON SCHEMA PUBLIC TO ROLE sysadmin;
GRANT CREATE STREAMLIT ON SCHEMA PUBLIC TO ROLE sysadmin;
```

### 3. Generate PAT Token for Cortex

In Snowflake Snowsight:
1. Click profile → **Edit profile**
2. **Security** → **Integrations**
3. **Programmatic Access Tokens** → **Create**
4. Copy token and add to GitHub secret `CORTEX_ANALYST_TOKEN`

## Deployment Workflow

The CI/CD pipeline runs automatically when you push to `main`:

```
Push to main
    ↓
[Test] Run linting & unit tests
    ↓
[Test] Verify Cortex Analyst connection
    ↓
[Deploy] Create deployment package
    ↓
[Deploy] Upload files to Snowflake stage
    ↓
[Deploy] Create/update Streamlit app
    ↓
[Deploy] Run smoke tests
    ↓
Success ✓
```

## Manual Deployment

If you need to deploy outside of CI/CD:

```bash
# 1. Create deployment package
mkdir -p dist/src
cp streamlit_app.py dist/
cp requirements.txt dist/
cp -r src/* dist/src/

# 2. Upload to stage
python scripts/deploy.py

# 3. Create/update Streamlit app
python scripts/create_streamlit_app.py

# 4. Run smoke tests
python scripts/smoke_test.py
```

## Accessing the App

After successful deployment:

1. Go to **Snowflake Console** (Snowsight)
2. Navigate to **Streamlit** (left sidebar)
3. Click **census_chat_prod**
4. App loads in your browser with direct Snowflake connection

No external hosting required! 🎉

## Monitoring & Debugging

### Check Deployment Status

```sql
-- View Streamlit apps
SELECT * FROM INFORMATION_SCHEMA.STREAMLITS 
WHERE NAME = 'census_chat_prod';

-- View recent query history
SELECT QUERY_TEXT, EXECUTION_TIME, ROWS_PRODUCED, ERROR_CODE
FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
WHERE USER_NAME = 'GITHUB_DEPLOY'
  AND START_TIME > DATEADD(hour, -1, CURRENT_TIMESTAMP())
ORDER BY START_TIME DESC
LIMIT 20;
```

### Monitor Cortex Usage

```sql
SELECT *
FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_USAGE
WHERE START_TIME > DATEADD(day, -7, CURRENT_DATE())
ORDER BY START_TIME DESC;
```

### App Logs

Click **⋮** menu on Streamlit app → **View logs** to see real-time app output.

## Troubleshooting

### Deployment Fails: "Stage not found"

**Fix**: Ensure `ACCOUNTADMIN` role in Snowflake secrets.

### Streamlit App Not Loading

**Check**:
```sql
-- Verify stage has files
LIST @CENSUS_NEIGHBORHOOD_INSIGHTS.PUBLIC.STREAMLIT_STAGE;

-- Verify semantic model exists
SELECT * FROM INFORMATION_SCHEMA.SEMANTIC_VIEWS 
WHERE NAME = 'CENSUS_DEMOGRAPHICS_MODEL';

-- Restart warehouse
ALTER WAREHOUSE CENSUS_DEV_WH RESUME;
```

### Cortex Queries Failing

**Check**:
```sql
-- Verify Cortex is enabled
SELECT SYSTEM$CORTEX_ENABLED();

-- Verify role has Cortex access
SHOW GRANTS ON ACCOUNT;
```

## Cost Optimization

1. **Warehouse**: Use smallest warehouse for production (`XSMALL` or `SMALL`)
2. **Auto-suspend**: Set warehouse to suspend after 5 minutes
3. **Cortex costs**: Monitor usage; costs apply per Cortex API call
4. **Deploy frequency**: Deployments only run on push to `main`

```sql
-- Optimize warehouse
ALTER WAREHOUSE CENSUS_DEV_WH
  SET AUTO_SUSPEND = 300
      AUTO_RESUME = TRUE
      WAREHOUSE_SIZE = 'XSMALL';
```

## Rollback

To rollback to previous version:

```bash
# Find previous commit
git log --oneline

# Revert deployment
git revert <commit-hash>
git push origin main

# CI/CD automatically redeploys previous version
```

Or manually:

```sql
-- Drop current app
DROP STREAMLIT census_chat_prod;

-- Recreate from previous stage snapshot
CREATE STREAMLIT census_chat_prod
  ROOT_LOCATION = @STREAMLIT_STAGE_BACKUP
  MAIN_FILE = '/streamlit_app.py'
  QUERY_WAREHOUSE = CENSUS_DEV_WH;
```

## Next Steps

1. ✅ Add secrets to GitHub
2. ✅ Create Snowflake service account
3. ✅ Push to `main` branch
4. ✅ Watch GitHub Actions workflow
5. ✅ Access app in Snowflake Console → Streamlit

---

**Questions?** Check GitHub Actions logs: Repository → **Actions** → Latest workflow run
