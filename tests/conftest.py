"""Shared test configuration and fixtures"""

import os
import pytest
from dotenv import load_dotenv


@pytest.fixture(scope="session", autouse=True)
def load_env():
    """Load environment variables from .env file"""
    load_dotenv()


@pytest.fixture
def snowflake_config():
    """Snowflake configuration from environment"""
    return {
        'account': os.getenv('SNOWFLAKE_ACCOUNT'),
        'user': os.getenv('SNOWFLAKE_USER'),
        'password': os.getenv('SNOWFLAKE_PASSWORD'),
        'database': os.getenv('SNOWFLAKE_DATABASE'),
        'schema': os.getenv('SNOWFLAKE_SCHEMA'),
        'warehouse': os.getenv('SNOWFLAKE_WAREHOUSE'),
    }


@pytest.fixture
def cortex_token():
    """Cortex Analyst token from environment"""
    return os.getenv('CORTEX_ANALYST_TOKEN')


@pytest.fixture
def cortex_analyst():
    """Import CortexAnalyst after environment is loaded"""
    from src.cortex_analyst import CortexAnalyst
    return CortexAnalyst
