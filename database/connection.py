"""
Database connection implementations.

Provides clean abstractions for both SQLite (local) and Turso (cloud) databases.
Uses the DatabaseProtocol to ensure consistent interface across implementations.
"""

import os
import logging
import asyncio
from typing import Optional
from abc import ABC, abstractmethod

import aiosqlite

from config import settings

logger = logging.getLogger(__name__)


class BaseDatabase(ABC):
    """Abstract base class for database implementations."""

    @abstractmethod
    async def execute(self, query: str, params: tuple = None) -> int:
        """Execute a query and return affected row count."""
        pass

    @abstractmethod
    async def fetch_one(self, query: str, params: tuple = None) -> Optional[dict]:
        """Fetch a single row."""
        pass

    @abstractmethod
    async def fetch_all(self, query: str, params: tuple = None) -> list[dict]:
        """Fetch all rows."""
        pass

    @abstractmethod
    async def insert_returning_id(self, query: str, params: tuple = None) -> int:
        """Insert and return the new row's ID."""
        pass

    @abstractmethod
    async def execute_many(self, statements: list[str]) -> None:
        """Execute multiple statements."""
        pass

    @abstractmethod
    async def close(self) -> None:
        """Close the connection."""
        pass


class SQLiteDatabase(BaseDatabase):
    """SQLite implementation using aiosqlite."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._ensure_directory()
        logger.info(f"Using SQLite database: {db_path}")

    def _ensure_directory(self) -> None:
        """Ensure the database directory exists."""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)

    async def execute(self, query: str, params: tuple = None) -> int:
        """Execute a query and return affected row count."""
        async with aiosqlite.connect(self.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            cursor = await conn.execute(query, params or ())
            await conn.commit()
            return cursor.rowcount

    async def fetch_one(self, query: str, params: tuple = None) -> Optional[dict]:
        """Fetch a single row."""
        async with aiosqlite.connect(self.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            cursor = await conn.execute(query, params or ())
            row = await cursor.fetchone()
            # Commit if this was a modifying query (INSERT/UPDATE/DELETE with RETURNING)
            query_upper = query.strip().upper()
            if query_upper.startswith(('INSERT', 'UPDATE', 'DELETE')):
                await conn.commit()
            return dict(row) if row else None

    async def fetch_all(self, query: str, params: tuple = None) -> list[dict]:
        """Fetch all rows."""
        async with aiosqlite.connect(self.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            cursor = await conn.execute(query, params or ())
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def insert_returning_id(self, query: str, params: tuple = None) -> int:
        """Insert and return the new row's ID using RETURNING clause."""
        # Add RETURNING id if not present
        query_with_returning = query.rstrip().rstrip(';')
        if 'RETURNING' not in query_with_returning.upper():
            query_with_returning += ' RETURNING id'

        async with aiosqlite.connect(self.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            cursor = await conn.execute(query_with_returning, params or ())
            row = await cursor.fetchone()
            await conn.commit()
            if row:
                return row[0]  # First column is the id
            raise RuntimeError("INSERT did not return an ID")

    async def execute_many(self, statements: list[str]) -> None:
        """Execute multiple statements."""
        async with aiosqlite.connect(self.db_path) as conn:
            for stmt in statements:
                if stmt.strip():
                    await conn.execute(stmt)
            await conn.commit()

    async def close(self) -> None:
        """Close the connection (no-op for SQLite with context managers)."""
        pass


class TursoDatabase(BaseDatabase):
    """Turso implementation using libsql-client (HTTP)."""

    def __init__(self, url: str, auth_token: str):
        self._url = url
        self._auth_token = auth_token
        self._client = None
        self._init_client()
        logger.info(f"Using Turso database: {url}")

    def _init_client(self) -> None:
        """Initialize the Turso client."""
        try:
            import libsql_client

            # Convert libsql:// URL to https:// for HTTP client
            turso_url = self._url
            if turso_url.startswith("libsql://"):
                turso_url = turso_url.replace("libsql://", "https://")

            self._client = libsql_client.create_client_sync(
                url=turso_url,
                auth_token=self._auth_token
            )
            logger.info(f"Turso connection established: {turso_url}")
        except ImportError:
            logger.error("libsql-client not installed. Install with: pip install libsql-client")
            raise
        except Exception as e:
            logger.error(f"Failed to connect to Turso: {e}")
            raise

    def _execute_sync(self, query: str, params: tuple = None):
        """Execute query synchronously on Turso."""
        if params:
            return self._client.execute(query, list(params))
        else:
            return self._client.execute(query)

    async def execute(self, query: str, params: tuple = None) -> int:
        """Execute a query and return affected row count."""
        result = await asyncio.to_thread(self._execute_sync, query, params)
        if result is None:
            return 0
        return result.rows_affected if hasattr(result, 'rows_affected') else 0

    async def fetch_one(self, query: str, params: tuple = None) -> Optional[dict]:
        """Fetch a single row."""
        result = await asyncio.to_thread(self._execute_sync, query, params)
        if not result or not result.rows:
            return None
        columns = result.columns
        return dict(zip(columns, result.rows[0]))

    async def fetch_all(self, query: str, params: tuple = None) -> list[dict]:
        """Fetch all rows."""
        result = await asyncio.to_thread(self._execute_sync, query, params)
        if not result or not result.rows:
            return []
        columns = result.columns
        return [dict(zip(columns, row)) for row in result.rows]

    async def insert_returning_id(self, query: str, params: tuple = None) -> int:
        """Insert and return the new row's ID."""
        # Add RETURNING id if not present
        query_with_returning = query.rstrip().rstrip(';')
        if 'RETURNING' not in query_with_returning.upper():
            query_with_returning += ' RETURNING id'

        result = await asyncio.to_thread(self._execute_sync, query_with_returning, params)

        # Try to get ID from result rows first
        if result and result.rows:
            return result.rows[0][0]

        # Fall back to last_insert_rowid if available
        if result and hasattr(result, 'last_insert_rowid') and result.last_insert_rowid:
            return result.last_insert_rowid

        raise RuntimeError("INSERT did not return an ID")

    async def execute_many(self, statements: list[str]) -> None:
        """Execute multiple statements."""
        for stmt in statements:
            if stmt.strip():
                await asyncio.to_thread(self._execute_sync, stmt, None)

    async def close(self) -> None:
        """Close the Turso client."""
        if self._client:
            # libsql-client sync client doesn't have explicit close
            self._client = None


def create_database() -> BaseDatabase:
    """
    Factory function to create the appropriate database instance.

    Returns:
        SQLiteDatabase if USE_TURSO is False or Turso not configured,
        TursoDatabase otherwise.
    """
    if settings.use_turso and settings.turso_db_url:
        return TursoDatabase(
            url=settings.turso_db_url,
            auth_token=settings.turso_auth_token
        )
    return SQLiteDatabase(settings.database_path)


# Create singleton instance
db = create_database()
