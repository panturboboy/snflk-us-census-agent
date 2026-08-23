#!/usr/bin/env python3
"""Setup GitHub secrets for CI/CD deployment."""

import subprocess
import sys
import os
from pathlib import Path
from getpass import getpass

def run_command(cmd):
    """Run shell command."""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
    except Exception as e:
        return False, "", str(e)

def check_gh_cli():
    """Check if GitHub CLI is installed."""
    success, _, _ = run_command("gh --version")
    return success

def get_repo():
    """Get current repo name."""
    success, repo, _ = run_command("gh repo view --json nameWithOwner -q")
    return repo if success else None

def set_secret(name, value):
    """Set a GitHub secret."""
    cmd = f'gh secret set {name} --body "{value}"'
    success, _, _ = run_command(cmd)
    return success

def main():
    print("\n=== GitHub Secrets Setup ===\n")

    # Check prerequisites
    print("Checking prerequisites...")
    if not check_gh_cli():
        print("✗ GitHub CLI not found")
        print("  Install from: https://cli.github.com")
        print("  Or: brew install gh")
        sys.exit(1)
    print("✓ GitHub CLI found")

    # Get repo info
    repo = get_repo()
    if not repo:
        print("✗ Could not determine repository")
        print("  Make sure you're in a git repository and authenticated with 'gh auth login'")
        sys.exit(1)
    print(f"✓ Repository: {repo}\n")

    # Collect credentials
    print("Enter your Snowflake credentials:\n")

    account = input("  Account ID (e.g., MIYVSAQ-NX19708): ").strip()
    user = input("  User (e.g., IAROSLAVKASIANENKO): ").strip()
    password = getpass("  Password: ")
    database = input("  Database (e.g., CENSUS_NEIGHBORHOOD_INSIGHTS): ").strip()
    schema = input("  Schema (e.g., PUBLIC): ").strip()
    warehouse = input("  Warehouse (e.g., CENSUS_DEV_WH): ").strip()
    token = getpass("  Cortex Analyst Token (PAT): ")

    # Validate
    if not all([account, user, password, database, schema, warehouse, token]):
        print("\n✗ All fields are required")
        sys.exit(1)

    # Confirm
    print("\n" + "="*50)
    print("Summary:")
    print(f"  Account:   {account}")
    print(f"  User:      {user}")
    print(f"  Database:  {database}")
    print(f"  Schema:    {schema}")
    print(f"  Warehouse: {warehouse}")
    print("="*50 + "\n")

    response = input("Create these secrets? (y/n): ").strip().lower()
    if response != 'y':
        print("Cancelled.")
        sys.exit(0)

    # Create secrets
    print("\nCreating secrets...\n")

    secrets = {
        'SNOWFLAKE_ACCOUNT': account,
        'SNOWFLAKE_USER': user,
        'SNOWFLAKE_PASSWORD': password,
        'SNOWFLAKE_DATABASE': database,
        'SNOWFLAKE_SCHEMA': schema,
        'SNOWFLAKE_WAREHOUSE': warehouse,
        'CORTEX_ANALYST_TOKEN': token,
    }

    failed = []
    for name, value in secrets.items():
        if set_secret(name, value):
            print(f"✓ {name}")
        else:
            print(f"✗ {name}")
            failed.append(name)

    if failed:
        print(f"\n✗ Failed to create: {', '.join(failed)}")
        sys.exit(1)

    # Success
    print("\n✓ All secrets created!\n")
    print("Next steps:")
    print("  1. Ensure Snowflake service account exists:")
    print('     CREATE USER github_deploy PASSWORD = \'<strong-password>\';')
    print("     GRANT ROLE ACCOUNTADMIN TO USER github_deploy;")
    print("")
    print("  2. Configure the remote and push:")
    print("     git remote add origin https://github.com/YOUR_USERNAME/CensusAgent.git")
    print("     git branch -M main")
    print("     git push -u origin main")
    print("")
    print(f"  3. Monitor deployment at:")
    print(f"     https://github.com/{repo}/actions")
    print("")

if __name__ == "__main__":
    main()
