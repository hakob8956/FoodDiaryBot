"""
Database protocol definitions.

Defines the interface that all database implementations must follow,
enabling clean abstraction between SQLite and Turso backends.
"""

from typing import Protocol, Optional, Any, runtime_checkable
from abc import abstractmethod


@runtime_checkable
class DatabaseProtocol(Protocol):
    """
    Protocol defining the interface for database operations.

    All database implementations (SQLite, Turso) must implement this interface.
    This enables dependency injection and makes testing easier.
    """

    @abstractmethod
    async def execute(self, query: str, params: tuple = None) -> int:
        """
        Execute a query that modifies data (INSERT, UPDATE, DELETE).

        Args:
            query: SQL query string with ? placeholders
            params: Tuple of parameter values

        Returns:
            Number of affected rows
        """
        ...

    @abstractmethod
    async def fetch_one(self, query: str, params: tuple = None) -> Optional[dict]:
        """
        Fetch a single row from a SELECT query.

        Args:
            query: SQL SELECT query string
            params: Tuple of parameter values

        Returns:
            Dictionary with column names as keys, or None if no results
        """
        ...

    @abstractmethod
    async def fetch_all(self, query: str, params: tuple = None) -> list[dict]:
        """
        Fetch all rows from a SELECT query.

        Args:
            query: SQL SELECT query string
            params: Tuple of parameter values

        Returns:
            List of dictionaries with column names as keys
        """
        ...

    @abstractmethod
    async def insert_returning_id(self, query: str, params: tuple = None) -> int:
        """
        Execute an INSERT and return the new row's ID.

        This method handles the differences between SQLite (lastrowid)
        and Turso (RETURNING clause) transparently.

        Args:
            query: SQL INSERT query string (without RETURNING clause)
            params: Tuple of parameter values

        Returns:
            The ID of the newly inserted row
        """
        ...

    @abstractmethod
    async def execute_many(self, statements: list[str]) -> None:
        """
        Execute multiple SQL statements (used for migrations).

        Args:
            statements: List of SQL statements to execute
        """
        ...

    @abstractmethod
    async def close(self) -> None:
        """Close the database connection."""
        ...
