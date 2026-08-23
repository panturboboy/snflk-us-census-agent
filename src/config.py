import os
from dotenv import load_dotenv

load_dotenv()

class SnowflakeConfig:
    ACCOUNT = os.getenv("SNOWFLAKE_ACCOUNT")
    USER = os.getenv("SNOWFLAKE_USER")
    PASSWORD = os.getenv("SNOWFLAKE_PASSWORD")
    DATABASE = os.getenv("SNOWFLAKE_DATABASE")
    SCHEMA = os.getenv("SNOWFLAKE_SCHEMA")
    WAREHOUSE = os.getenv("SNOWFLAKE_WAREHOUSE")
    ROLE = os.getenv("SNOWFLAKE_ROLE", "SYSADMIN")

    @classmethod
    def validate(cls):
        required = [cls.ACCOUNT, cls.USER, cls.PASSWORD, cls.DATABASE, cls.SCHEMA, cls.WAREHOUSE]
        if not all(required):
            raise ValueError(
                "Missing Snowflake configuration. Please set all required env vars: "
                "SNOWFLAKE_ACCOUNT, SNOWFLAKE_USER, SNOWFLAKE_PASSWORD, "
                "SNOWFLAKE_DATABASE, SNOWFLAKE_SCHEMA, SNOWFLAKE_WAREHOUSE"
            )
