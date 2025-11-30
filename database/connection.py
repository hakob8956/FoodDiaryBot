import aiosqlite
import os
from contextlib import asynccontextmanager
from config import settings


class Database:
    """Async SQLite database connection manager."""

    def __init__(self, db_path: str = None):
        self.db_path = db_path or settings.database_path
        self._ensure_directory()

    def _ensure_directory(self):
        """Ensure the database directory exists."""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)

    @asynccontextmanager
    async def get_connection(self):
        """Get an async database connection."""
        conn = await aiosqlite.connect(self.db_path)
        conn.row_factory = aiosqlite.Row
        try:
            yield conn
        finally:
            await conn.close()

    async def execute(self, query: str, params: tuple = None):
        """Execute a single query."""
        async with self.get_connection() as conn:
            cursor = await conn.execute(query, params or ())
            await conn.commit()
            return cursor

    async def fetch_one(self, query: str, params: tuple = None):
        """Fetch a single row."""
        async with self.get_connection() as conn:
            cursor = await conn.execute(query, params or ())
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def fetch_all(self, query: str, params: tuple = None):
        """Fetch all rows."""
        async with self.get_connection() as conn:
            cursor = await conn.execute(query, params or ())
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]


# Singleton instance
db = Database()
