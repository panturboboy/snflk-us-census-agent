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
            missing = [name for name, val in [
                ("SNOWFLAKE_ACCOUNT", cls.ACCOUNT),
                ("SNOWFLAKE_USER", cls.USER),
                ("SNOWFLAKE_PASSWORD", cls.PASSWORD),
                ("SNOWFLAKE_DATABASE", cls.DATABASE),
                ("SNOWFLAKE_SCHEMA", cls.SCHEMA),
                ("SNOWFLAKE_WAREHOUSE", cls.WAREHOUSE),
            ] if not val]
            raise ValueError(
                f"Missing Snowflake configuration: {', '.join(missing)}. "
                "Check Streamlit Cloud Secrets or local .env file."
            )
