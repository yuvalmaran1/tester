from typing import Union
from .base import DatabaseInterface
from .sqlite_db import SQLiteDatabase
from .postgres_db import PostgreSQLDatabase


class DatabaseFactory:
    """Factory class for creating database instances based on configuration string."""

    @staticmethod
    def create_database(config_string: str) -> DatabaseInterface:
        """Create a database instance based on the configuration string.

        Args:
            config_string: Database configuration string
                - For SQLite: file path (e.g., "./test.db")
                - For PostgreSQL: connection string (e.g., "postgresql://user:pass@host:port/db")

        Returns:
            DatabaseInterface: Appropriate database implementation

        Raises:
            ValueError: If the configuration string format is not supported
        """
        if not config_string:
            raise ValueError("Database configuration string cannot be empty")

        # Check for PostgreSQL connection string
        if config_string.startswith(('postgresql://', 'postgres://')):
            return PostgreSQLDatabase(config_string)

        # Check for SQLite file path (ends with .db or is a relative/absolute path)
        elif config_string.endswith('.db') or '/' in config_string or '\\' in config_string:
            return SQLiteDatabase(config_string)

        # Default to SQLite for backward compatibility
        else:
            return SQLiteDatabase(config_string)

    @staticmethod
    def get_database_type(config_string: str) -> str:
        """Get the database type from configuration string.

        Args:
            config_string: Database configuration string

        Returns:
            str: Database type ('sqlite' or 'postgresql')
        """
        if config_string.startswith(('postgresql://', 'postgres://')):
            return 'postgresql'
        else:
            return 'sqlite'
