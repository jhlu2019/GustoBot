import pymysql
import sqlalchemy
from sqlalchemy import create_engine, inspect
from typing import Dict, Any, List
import urllib.parse

from app.core.security import verify_password
from app.models.db_connection import DBConnection


def get_db_engine(connection: DBConnection, password: str = None):
    """
    Create a SQLAlchemy engine for the given database connection.
    """
    try:
        # 直接使用明文密码，不进行加密/解密处理
        # 在实际应用中，应该对密码进行适当的加密和解密

        # 如果是从配置文件读取的连接信息
        if hasattr(connection, 'password') and connection.password:
            actual_password = connection.password
        # 如果是从数据库读取的连接信息
        elif password:
            actual_password = password
        # 如果是使用已加密的密码
        else:
            # 这里我们假设password_encrypted存储的是明文密码
            # 在实际应用中，应该进行解密
            actual_password = connection.password_encrypted

        # Encode password for URL safety
        encoded_password = urllib.parse.quote_plus(actual_password)

        if connection.db_type.lower() == "mysql":
            conn_str = (
                f"mysql+pymysql://{connection.username}:"
                f"{encoded_password}@"
                f"{connection.host}:{connection.port}/{connection.database_name}"
            )
            print(f"Connecting to MySQL database: {connection.host}:{connection.port}/{connection.database_name}")
            return create_engine(conn_str)

        elif connection.db_type.lower() == "postgresql":
            conn_str = (
                f"postgresql://{connection.username}:"
                f"{encoded_password}@"
                f"{connection.host}:{connection.port}/{connection.database_name}"
            )
            print(f"Connecting to PostgreSQL database: {connection.host}:{connection.port}/{connection.database_name}")
            return create_engine(conn_str)

        elif connection.db_type.lower() == "sqlite":
            # For SQLite, the database_name is treated as the file path
            conn_str = f"sqlite:///{connection.database_name}"
            print(f"Connecting to SQLite database: {connection.database_name}")
            return create_engine(conn_str)

        else:
            raise ValueError(f"Unsupported database type: {connection.db_type}")
    except Exception as e:
        print(f"Error creating database engine: {str(e)}")
        raise


def test_db_connection(connection: DBConnection) -> bool:
    """
    Test if a database connection is valid.
    """
    try:
        print(f"Testing connection to {connection.db_type} database at {connection.host}:{connection.port}/{connection.database_name}")
        engine = get_db_engine(connection)
        with engine.connect() as conn:
            result = conn.execute(sqlalchemy.text("SELECT 1"))
            print(f"Connection test successful: {result.fetchone()}")
        return True
    except Exception as e:
        error_msg = f"Connection test failed: {str(e)}"
        print(error_msg)
        raise Exception(error_msg)


def execute_query(connection: DBConnection, query: str) -> List[Dict[str, Any]]:
    """
    Execute a SQL query on the target database and return the results.
    """
    try:
        engine = get_db_engine(connection)
        with engine.connect() as conn:
            result = conn.execute(sqlalchemy.text(query))
            columns = result.keys()
            return [dict(zip(columns, row)) for row in result.fetchall()]
    except Exception as e:
        raise Exception(f"Query execution failed: {str(e)}")
