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
    - Turso (cloud SQLite via libsql)
    - Local SQLite (via aiosqlite)

    Toggle with USE_TURSO environment variable.
    """

    def __init__(self):
        self.use_turso = settings.use_turso and bool(settings.turso_db_url)

        if self.use_turso:
            logger.info(f"Using Turso database: {settings.turso_db_url}")
            self._init_turso()
        else:
            logger.info(f"Using local SQLite database: {settings.database_path}")
            self.db_path = settings.database_path
            self._ensure_directory()
            self._turso_conn = None

    def _init_turso(self):
        """Initialize Turso connection."""
        try:
            import libsql_experimental as libsql
            self._turso_conn = libsql.connect(
                settings.turso_db_url,
                auth_token=settings.turso_auth_token
            )
            logger.info("Turso connection established")
        except ImportError:
            logger.error("libsql_experimental not installed. Install with: pip install libsql-experimental")
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
            # For Turso, yield the sync connection (used carefully)
            yield self._turso_conn
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
        """Execute query on Turso (sync)."""
        try:
            cursor = self._turso_conn.execute(query, params or ())
            self._turso_conn.commit()
            return cursor
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
            cursor = self._turso_conn.execute(query, params or ())
            row = cursor.fetchone()
            if row is None:
                return None
            # Convert to dict using column names
            columns = [desc[0] for desc in cursor.description]
            return dict(zip(columns, row))
        except Exception as e:
            logger.error(f"Turso fetch_one error: {e}")
            raise

    async def _fetch_one_sqlite(self, query: str, params: tuple = None) -> Optional[dict]:
        """Fetch one row from SQLite."""
        async with self.get_connection() as conn:
            cursor = await conn.execute(query, params or ())
            row = await cursor.fetchone()
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
            cursor = self._turso_conn.execute(query, params or ())
            rows = cursor.fetchall()
            if not rows:
                return []
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in rows]
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
                    self._turso_conn.execute(stmt)
            self._turso_conn.commit()
        else:
            async with self.get_connection() as conn:
                for stmt in statements:
                    if stmt.strip():
                        await conn.execute(stmt)
                await conn.commit()

    def get_lastrowid(self, cursor) -> Optional[int]:
        """Get the last inserted row ID from a cursor."""
        if self.use_turso:
            return cursor.lastrowid
        else:
            return cursor.lastrowid


# Singleton instance
db = Database()
