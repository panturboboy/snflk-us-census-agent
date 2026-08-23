#!/bin/bash
# Setup GitHub Secrets for CI/CD Deployment

set -e

echo "=== GitHub Secrets Setup ==="
echo ""
echo "This script will create GitHub secrets for automated deployment."
echo "Prerequisites: gh CLI installed and authenticated"
echo ""

# Check if gh CLI is installed
if ! command -v gh &> /dev/null; then
    echo "✗ GitHub CLI not found. Install from: https://cli.github.com"
    exit 1
fi

# Get repo info
REPO=$(gh repo view --json nameWithOwner -q)
echo "Repository: $REPO"
echo ""

# Read Snowflake credentials
echo "Enter your Snowflake credentials:"
read -p "  Account ID (e.g., MIYVSAQ-NX19708): " ACCOUNT
read -p "  User (e.g., IAROSLAVKASIANENKO): " USER
read -sp "  Password: " PASSWORD
echo ""
read -p "  Database (e.g., CENSUS_NEIGHBORHOOD_INSIGHTS): " DATABASE
read -p "  Schema (e.g., PUBLIC): " SCHEMA
read -p "  Warehouse (e.g., CENSUS_DEV_WH): " WAREHOUSE
read -sp "  Cortex Analyst Token (PAT): " TOKEN
echo ""

# Confirm
echo ""
echo "Summary:"
echo "  Account: $ACCOUNT"
echo "  User: $USER"
echo "  Database: $DATABASE"
echo "  Schema: $SCHEMA"
echo "  Warehouse: $WAREHOUSE"
read -p "Continue? (y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 1
fi

# Set secrets
echo ""
echo "Creating secrets..."

gh secret set SNOWFLAKE_ACCOUNT --body "$ACCOUNT"
echo "✓ SNOWFLAKE_ACCOUNT"

gh secret set SNOWFLAKE_USER --body "$USER"
echo "✓ SNOWFLAKE_USER"

gh secret set SNOWFLAKE_PASSWORD --body "$PASSWORD"
echo "✓ SNOWFLAKE_PASSWORD"

gh secret set SNOWFLAKE_DATABASE --body "$DATABASE"
echo "✓ SNOWFLAKE_DATABASE"

gh secret set SNOWFLAKE_SCHEMA --body "$SCHEMA"
echo "✓ SNOWFLAKE_SCHEMA"

gh secret set SNOWFLAKE_WAREHOUSE --body "$WAREHOUSE"
echo "✓ SNOWFLAKE_WAREHOUSE"

gh secret set CORTEX_ANALYST_TOKEN --body "$TOKEN"
echo "✓ CORTEX_ANALYST_TOKEN"

echo ""
echo "✓ All secrets created!"
echo ""
echo "Next steps:"
echo "  1. Create Snowflake service account:"
echo "     CREATE USER github_deploy PASSWORD = '<strong-password>';"
echo "     GRANT ROLE ACCOUNTADMIN TO USER github_deploy;"
echo ""
echo "  2. Push to main branch to trigger deployment:"
echo "     git push -u origin main"
echo ""
echo "  3. Monitor at: https://github.com/$REPO/actions"
