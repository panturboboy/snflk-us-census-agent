import snowflake.connector
from src.config import SnowflakeConfig


class SnowflakeClient:
    _connection = None

    @classmethod
    def get_connection(cls):
        if cls._connection is None:
            SnowflakeConfig.validate()
            cls._connection = snowflake.connector.connect(
                account=SnowflakeConfig.ACCOUNT,
                user=SnowflakeConfig.USER,
                password=SnowflakeConfig.PASSWORD,
                database=SnowflakeConfig.DATABASE,
                schema=SnowflakeConfig.SCHEMA,
                warehouse=SnowflakeConfig.WAREHOUSE,
                role=SnowflakeConfig.ROLE,
            )
        return cls._connection

    @classmethod
    def query(cls, sql: str) -> list:
        """Execute query and return results as list of dicts"""
        conn = cls.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(sql)
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            return [dict(zip(columns, row)) for row in rows]
        finally:
            cursor.close()

    @classmethod
    def close(cls):
        if cls._connection:
            cls._connection.close()
            cls._connection = None
