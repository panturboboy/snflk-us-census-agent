# Production Deployment Checklist

Complete these steps to deploy the Census Demographics Chat Agent to production.

## Phase 1: Snowflake Setup

### 1. Create Service Account for GitHub Actions

```sql
-- Run as ACCOUNTADMIN in Snowflake
CREATE USER github_deploy 
  PASSWORD = '<generate-a-strong-password-here>'
  COMMENT = 'Service account for GitHub Actions CI/CD deployment';

-- Grant necessary permissions
GRANT ROLE ACCOUNTADMIN TO USER github_deploy;

-- Or, if you prefer more restrictive permissions:
GRANT ROLE SYSADMIN TO USER github_deploy;
GRANT CREATE STAGE ON SCHEMA PUBLIC TO ROLE SYSADMIN;
GRANT CREATE STREAMLIT ON SCHEMA PUBLIC TO ROLE SYSADMIN;
```

⚠️ **Important**: Save the password - you'll need it for GitHub secrets.

### 2. Generate Cortex Analyst Token (PAT)

1. Go to **Snowflake Snowsight** (web console)
2. Click your **profile icon** (top right)
3. Select **Edit profile**
4. Go to **Security** tab
5. Click **Integrations** → **Programmatic Access Tokens**
6. Click **Create** button
7. Copy the token immediately (you won't see it again)

⚠️ **Important**: Keep this token secure - it's like a password.

### 3. Verify Semantic Model is Deployed

```sql
-- Check that the semantic model exists
SELECT * FROM INFORMATION_SCHEMA.SEMANTIC_VIEWS 
WHERE NAME = 'CENSUS_DEMOGRAPHICS_MODEL'
  AND SCHEMA_NAME = 'SEMANTIC'
  AND DATABASE_NAME = 'CENSUS_NEIGHBORHOOD_INSIGHTS';
```

Should return 1 row. If not, you may need to deploy DDLs first.

---

## Phase 2: GitHub Setup

### 1. Create GitHub Repository

```bash
# If you don't have a repo yet:
# Go to https://github.com/new
# Create a new repository (public or private)
# Note the URL: https://github.com/YOUR_USERNAME/CensusAgent.git
```

### 2. Add Remote and Push Code

```bash
cd /Users/Iaroslav/Projects/Snowflake/CensusAgent

# Add your GitHub repo as origin
git remote add origin https://github.com/YOUR_USERNAME/CensusAgent.git

# Set main as default branch
git branch -M main

# Push the code
git push -u origin main
```

### 3. Create GitHub Secrets

**Option A: Automatic (Recommended)**

```bash
# Requires: GitHub CLI installed
# Install: https://cli.github.com or `brew install gh`

# First, authenticate:
gh auth login

# Then run the setup script:
python scripts/setup_github_secrets.py

# Follow the prompts and enter your Snowflake credentials
```

**Option B: Manual**

Go to your GitHub repo → **Settings** → **Secrets and variables** → **Actions**

Click **New repository secret** for each:

| Name | Value |
|------|-------|
| `SNOWFLAKE_ACCOUNT` | Your account ID (e.g., `MIYVSAQ-NX19708`) |
| `SNOWFLAKE_USER` | Username (e.g., `github_deploy`) |
| `SNOWFLAKE_PASSWORD` | Password (the one you created) |
| `SNOWFLAKE_DATABASE` | Database name (e.g., `CENSUS_NEIGHBORHOOD_INSIGHTS`) |
| `SNOWFLAKE_SCHEMA` | Schema (e.g., `PUBLIC`) |
| `SNOWFLAKE_WAREHOUSE` | Warehouse (e.g., `CENSUS_DEV_WH`) |
| `CORTEX_ANALYST_TOKEN` | PAT token (from Snowsight) |

---

## Phase 3: Deploy

### 1. Trigger Deployment

```bash
# The code is already pushed to main
# GitHub Actions will automatically:
# 1. Run tests
# 2. Create deployment package
# 3. Upload to Snowflake stage
# 4. Create Streamlit app
# 5. Run smoke tests

# Monitor at: https://github.com/YOUR_USERNAME/CensusAgent/actions
```

### 2. Check Deployment Status

Go to your repo → **Actions** tab

You should see a workflow running: "Deploy to Snowflake"

Status will show:
- 🟡 In Progress (running tests)
- 🟡 In Progress (deploying)
- 🟢 Success (all tests passed)
- 🔴 Failed (check logs)

### 3. View Logs

Click the workflow run → see detailed logs for each step.

Common issues:
- ❌ "Secret not found" → Check GitHub Secrets configuration
- ❌ "Connection refused" → Check Snowflake account ID
- ❌ "Authentication failed" → Check username/password

---

## Phase 4: Access the App

### 1. Go to Snowflake Snowsight

https://ACCOUNT_ID.snowflakecomputing.com (e.g., https://miyvsaq-nx19708.snowflakecomputing.com)

### 2. Navigate to Streamlit

Left sidebar → **Streamlit** → **Streamlit apps**

### 3. Click the App

You should see: **census_chat_prod**

Click it to open the chat interface.

### 4. Start Asking Questions

Try these:
- "What is the population of California?"
- "Show racial composition of Texas"
- "How many households in New York?"

---

## Verification Checklist

- [ ] Snowflake service account created
- [ ] Cortex Analyst token generated
- [ ] Semantic model verified
- [ ] GitHub repo created
- [ ] Code pushed to main
- [ ] GitHub secrets created (all 7)
- [ ] GitHub Actions workflow succeeded
- [ ] App accessible in Snowflake Streamlit
- [ ] Sample queries working

---

## Troubleshooting

### GitHub Actions Failed

Check logs at: Repository → Actions → Latest run

**Common fixes:**
- Missing secrets: Check Settings → Secrets (all 7 should exist)
- Wrong credentials: Verify Snowflake account ID, user, password
- Token expired: Generate a new Cortex Analyst token

### App Not Showing in Snowflake

1. Go to Snowflake console
2. Run this SQL:
   ```sql
   SELECT * FROM INFORMATION_SCHEMA.STREAMLITS 
   WHERE NAME = 'census_chat_prod';
   ```
3. If empty, deployment didn't complete - check GitHub Actions logs
4. If exists but not visible, refresh Snowflake console (Ctrl+R)

### Queries Returning No Data

1. Check that Cortex Analyst is enabled:
   ```sql
   SELECT SYSTEM$CORTEX_ENABLED();
   ```
   Should return `TRUE`

2. Verify semantic model:
   ```sql
   SELECT * FROM INFORMATION_SCHEMA.SEMANTIC_VIEWS 
   WHERE NAME = 'CENSUS_DEMOGRAPHICS_MODEL';
   ```

3. Run smoke tests locally:
   ```bash
   python scripts/smoke_test.py
   ```

---

## Monitoring

### View Deployment History

Repository → Actions → Select workflow runs

### Monitor Query Execution

Snowflake Console → **Activity** → **Query History**

Filter by user: `GITHUB_DEPLOY` or your current user

### Check Cortex Usage

```sql
SELECT *
FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_USAGE
WHERE START_TIME > DATEADD(day, -7, CURRENT_DATE())
ORDER BY START_TIME DESC;
```

---

## What Happens on Every Push to Main

1. **Tests Run**
   - Linting (flake8)
   - Unit tests (pytest)
   - Cortex connection test

2. **Deployment**
   - Create deployment package
   - Upload files to Snowflake stage
   - Create/update Streamlit app
   - Run smoke tests

3. **Notifications**
   - ✓ Success → App ready to use
   - ✗ Failure → Check GitHub Actions logs

---

## Next: Customize & Scale

After deployment is working:

1. **Customize the app**: Edit `streamlit_app.py`
2. **Add more data**: Update semantic layer with additional facts
3. **Scale up**: Increase warehouse size if needed
4. **Monitor**: Set up alerts for failed deployments

Every push to `main` automatically redeploys! 🚀

---

## Quick Reference

| Task | Command |
|------|---------|
| Setup secrets | `python scripts/setup_github_secrets.py` |
| Deploy locally | `python scripts/deploy.py` |
| Create app | `python scripts/create_streamlit_app.py` |
| Run tests | `python scripts/smoke_test.py` |
| View logs | GitHub Actions tab in repo |
| Access app | Snowflake Snowsight → Streamlit |

---

**Status**: Ready for deployment ✓

All files committed and pushed. Awaiting GitHub Actions workflow completion.
