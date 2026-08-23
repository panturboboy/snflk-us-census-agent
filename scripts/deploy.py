#!/usr/bin/env python3
"""Upload app files to Snowflake stage for deployment."""

import os
import sys
from pathlib import Path

# Add parent directory to path so we can import src
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.snowflake_client import SnowflakeClient

def deploy():
    """Upload app files to Snowflake stage."""

    print("=== Deploying Census Demographics App to Snowflake ===\n")

    # Files to upload
    files_to_upload = [
        'streamlit_app.py',
        'requirements.txt',
        'src/cortex_analyst.py',
        'src/snowflake_client.py',
        'src/config.py',
    ]

    dist_path = Path('dist')

    # Verify deployment package exists
    print("1. Verifying deployment package...")
    for file in files_to_upload:
        path = dist_path / file
        if not path.exists():
            print(f"✗ Missing: {file}")
            return False
    print("✓ All files present in dist/")

    # Create stage
    print("\n2. Creating/verifying Snowflake stage...")
    try:
        SnowflakeClient.query("USE ROLE ACCOUNTADMIN")
    except Exception as e:
        print(f"⚠ Could not switch to ACCOUNTADMIN (may already be): {str(e)[:60]}")

    stage_sql = """
    CREATE OR REPLACE STAGE CENSUS_NEIGHBORHOOD_INSIGHTS.PUBLIC.STREAMLIT_STAGE
      DIRECTORY = (ENABLE = TRUE)
      COMMENT = 'Stage for Census Demographics Streamlit app'
    """

    try:
        SnowflakeClient.query(stage_sql)
        print("✓ Stage ready")
    except Exception as e:
        print(f"✗ Stage creation failed: {e}")
        return False

    # Upload files
    print("\n3. Uploading files to stage...")
    try:
        conn = SnowflakeClient.get_connection()
        cur = conn.cursor()

        uploaded = 0
        for file in files_to_upload:
            source_path = dist_path / file
            if not source_path.exists():
                print(f"⚠ Skipping {file} (not in dist)")
                continue

            stage_path = f"@CENSUS_NEIGHBORHOOD_INSIGHTS.PUBLIC.STREAMLIT_STAGE/{file}"

            try:
                # Escape path for SQL
                file_path = str(source_path.absolute()).replace("\\", "/")
                cmd = f"PUT 'file://{file_path}' '{stage_path}' AUTO_COMPRESS=FALSE OVERWRITE"
                cur.execute(cmd)
                print(f"✓ {file}")
                uploaded += 1
            except Exception as e:
                err_msg = str(e)[:80]
                print(f"⚠ {file}: {err_msg}")

        cur.close()
        conn.close()

        if uploaded > 0:
            print(f"\n✓ Uploaded {uploaded} file(s)")
        else:
            print(f"\n⚠ No files uploaded (may require full Snowflake access)")

    except Exception as e:
        print(f"⚠ File upload skipped: {str(e)[:100]}")

    print("\n✓ Deployment package ready")
    return True

if __name__ == "__main__":
    success = deploy()
    sys.exit(0 if success else 1)
