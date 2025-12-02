import os
import logging
from contextlib import asynccontextmanager
from typing import Optional, Any

import aiosqlite

from config import settings

logger = logging.getLogger(__name__)


class Database:
    """
    Async database connection manager with dual support for:
    - Turso (cloud SQLite via libsql-client HTTP API)
    - Local SQLite (via aiosqlite)

    Toggle with USE_TURSO environment variable.
    """

    def __init__(self):
        self.use_turso = settings.use_turso and bool(settings.turso_db_url)
        self._turso_client = None

        if self.use_turso:
            logger.info(f"Using Turso database: {settings.turso_db_url}")
            self._init_turso()
        else:
            logger.info(f"Using local SQLite database: {settings.database_path}")
            self.db_path = settings.database_path
            self._ensure_directory()

    def _init_turso(self):
        """Initialize Turso connection using libsql-client (HTTP)."""
        try:
            import libsql_client

            # Convert libsql:// URL to https:// for HTTP client
            turso_url = settings.turso_db_url
            if turso_url.startswith("libsql://"):
                turso_url = turso_url.replace("libsql://", "https://")

            self._turso_client = libsql_client.create_client_sync(
                url=turso_url,
                auth_token=settings.turso_auth_token
            )
            logger.info(f"Turso connection established (HTTP client): {turso_url}")
        except ImportError:
            logger.error("libsql-client not installed. Install with: pip install libsql-client")
            raise
        except Exception as e:
            logger.error(f"Failed to connect to Turso: {e}")
            raise

    def _ensure_directory(self):
        """Ensure the database directory exists (for local SQLite)."""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)

    @asynccontextmanager
    async def get_connection(self):
        """Get an async database connection (SQLite only, for migrations)."""
        if self.use_turso:
            # For Turso, yield None - use the client methods directly
            yield None
        else:
            conn = await aiosqlite.connect(self.db_path)
            conn.row_factory = aiosqlite.Row
            try:
                yield conn
            finally:
                await conn.close()

    async def execute(self, query: str, params: tuple = None) -> Any:
        """Execute a single query (INSERT, UPDATE, DELETE)."""
        if self.use_turso:
            return self._execute_turso(query, params)
        else:
            return await self._execute_sqlite(query, params)

    def _execute_turso(self, query: str, params: tuple = None) -> Any:
        """Execute query on Turso (sync HTTP client)."""
        try:
            # libsql-client uses positional args
            args = list(params) if params else []
            result = self._turso_client.execute(query, args)
            return TursoCursor(result)
        except Exception as e:
            logger.error(f"Turso execute error: {e}")
            raise

    async def _execute_sqlite(self, query: str, params: tuple = None) -> Any:
        """Execute query on SQLite (async)."""
        async with self.get_connection() as conn:
            cursor = await conn.execute(query, params or ())
            await conn.commit()
            return cursor

    async def fetch_one(self, query: str, params: tuple = None) -> Optional[dict]:
        """Fetch a single row."""
        if self.use_turso:
            return self._fetch_one_turso(query, params)
        else:
            return await self._fetch_one_sqlite(query, params)

    def _fetch_one_turso(self, query: str, params: tuple = None) -> Optional[dict]:
        """Fetch one row from Turso."""
        try:
            args = list(params) if params else []
            result = self._turso_client.execute(query, args)
            logger.debug(f"Turso result: rows={result.rows}, columns={result.columns}, last_insert_rowid={getattr(result, 'last_insert_rowid', None)}")

            # For INSERT with RETURNING, if rows is empty but we have last_insert_rowid
            if not result.rows:
                # Check if this is an INSERT RETURNING id query
                if 'RETURNING' in query.upper() and 'id' in query.lower():
                    last_id = getattr(result, 'last_insert_rowid', None)
                    if last_id:
                        return {"id": last_id}
                return None

            # Convert to dict using column names (columns are strings in libsql-client)
            columns = result.columns
            return dict(zip(columns, result.rows[0]))
        except Exception as e:
            logger.error(f"Turso fetch_one error: {e}")
            raise

    async def _fetch_one_sqlite(self, query: str, params: tuple = None) -> Optional[dict]:
        """Fetch one row from SQLite."""
        async with self.get_connection() as conn:
            cursor = await conn.execute(query, params or ())
            row = await cursor.fetchone()
            # Commit for INSERT/UPDATE/DELETE with RETURNING
            if query.strip().upper().startswith(('INSERT', 'UPDATE', 'DELETE')):
                await conn.commit()
            return dict(row) if row else None

    async def fetch_all(self, query: str, params: tuple = None) -> list[dict]:
        """Fetch all rows."""
        if self.use_turso:
            return self._fetch_all_turso(query, params)
        else:
            return await self._fetch_all_sqlite(query, params)

    def _fetch_all_turso(self, query: str, params: tuple = None) -> list[dict]:
        """Fetch all rows from Turso."""
        try:
            args = list(params) if params else []
            result = self._turso_client.execute(query, args)
            if not result.rows:
                return []
            # columns are strings in libsql-client
            columns = result.columns
            return [dict(zip(columns, row)) for row in result.rows]
        except Exception as e:
            logger.error(f"Turso fetch_all error: {e}")
            raise

    async def _fetch_all_sqlite(self, query: str, params: tuple = None) -> list[dict]:
        """Fetch all rows from SQLite."""
        async with self.get_connection() as conn:
            cursor = await conn.execute(query, params or ())
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def execute_many(self, statements: list[str]):
        """Execute multiple statements (for migrations)."""
        if self.use_turso:
            for stmt in statements:
                if stmt.strip():
                    self._turso_client.execute(stmt)
        else:
            async with self.get_connection() as conn:
                for stmt in statements:
                    if stmt.strip():
                        await conn.execute(stmt)
                await conn.commit()

    def get_lastrowid(self, cursor) -> Optional[int]:
        """Get the last inserted row ID from a cursor."""
        if self.use_turso:
            # TursoCursor wraps the result
            return cursor.lastrowid if cursor else None
        else:
            return cursor.lastrowid


class TursoCursor:
    """Wrapper to provide cursor-like interface for Turso results."""

    def __init__(self, result):
        self.result = result
        self.lastrowid = result.last_insert_rowid if result else None
        self.rowcount = result.rows_affected if result else 0


# Singleton instance
db = Database()
