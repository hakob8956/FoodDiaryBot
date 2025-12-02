import logging
from database.connection import db
from config import settings

logger = logging.getLogger(__name__)


# Individual table creation statements
CREATE_USERS_TABLE = """
CREATE TABLE IF NOT EXISTS users (
    telegram_id INTEGER PRIMARY KEY,
    username TEXT,
    first_name TEXT,
    weight REAL,
    height REAL,
    age INTEGER,
    sex TEXT CHECK(sex IN ('male', 'female')),
    activity_level TEXT CHECK(activity_level IN (
        'sedentary', 'lightly_active', 'moderately_active', 'very_active'
    )),
    goal TEXT CHECK(goal IN ('lose', 'maintain', 'gain')),
    daily_calorie_target INTEGER,
    calorie_override INTEGER DEFAULT 0,
    onboarding_complete INTEGER DEFAULT 0,
    notifications_enabled INTEGER DEFAULT 1,
    reminder_hour INTEGER DEFAULT 20,
    last_reminder_sent TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
"""

CREATE_ONBOARDING_STATE_TABLE = """
CREATE TABLE IF NOT EXISTS onboarding_state (
    telegram_id INTEGER PRIMARY KEY,
    current_step TEXT,
    collected_data TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
"""

CREATE_FOOD_LOGS_TABLE = """
CREATE TABLE IF NOT EXISTS food_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id INTEGER NOT NULL,
    logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    input_type TEXT CHECK(input_type IN ('photo', 'text', 'photo_text')),
    raw_input TEXT,
    photo_file_id TEXT,
    analysis_json TEXT NOT NULL,
    total_calories INTEGER,
    total_protein REAL,
    total_carbs REAL,
    total_fat REAL,
    confidence_score REAL,
    FOREIGN KEY (telegram_id) REFERENCES users(telegram_id)
)
"""

CREATE_FOOD_LOGS_INDEX = """
CREATE INDEX IF NOT EXISTS idx_food_logs_user_date
ON food_logs(telegram_id, logged_at)
"""


async def run_migrations():
    """Create all database tables and run migrations."""
    logger.info("Running database migrations...")

    # Create tables one by one (works with both SQLite and Turso)
    statements = [
        CREATE_USERS_TABLE,
        CREATE_ONBOARDING_STATE_TABLE,
        CREATE_FOOD_LOGS_TABLE,
        CREATE_FOOD_LOGS_INDEX,
    ]

    await db.execute_many(statements)

    # Run additional migrations for existing databases
    await _migrate_add_notification_columns()

    print("Database migrations completed successfully.")
    logger.info("Database migrations completed successfully.")


async def _migrate_add_notification_columns():
    """Add notification columns to existing users table if missing."""
    if db.use_turso:
        # For Turso, just try to add columns (will fail silently if they exist)
        await _migrate_turso_notification_columns()
    else:
        # For SQLite, use PRAGMA to check existing columns
        await _migrate_sqlite_notification_columns()


async def _migrate_turso_notification_columns():
    """Add notification columns for Turso (try/except for each)."""
    columns_to_add = [
        ("notifications_enabled", "INTEGER DEFAULT 1"),
        ("reminder_hour", "INTEGER DEFAULT 20"),
        ("last_reminder_sent", "TIMESTAMP"),
    ]

    for col_name, col_type in columns_to_add:
        try:
            db._turso_conn.execute(
                f"ALTER TABLE users ADD COLUMN {col_name} {col_type}"
            )
            db._turso_conn.commit()
            logger.info(f"Added column {col_name} to users table")
        except Exception as e:
            # Column likely already exists
            if "duplicate column" in str(e).lower() or "already exists" in str(e).lower():
                pass
            else:
                logger.debug(f"Column {col_name} might already exist: {e}")


async def _migrate_sqlite_notification_columns():
    """Add notification columns for SQLite (uses PRAGMA)."""
    import aiosqlite

    async with db.get_connection() as conn:
        # Check existing columns
        cursor = await conn.execute("PRAGMA table_info(users)")
        rows = await cursor.fetchall()
        columns = {row[1] for row in rows}

        # Add missing columns
        if "notifications_enabled" not in columns:
            await conn.execute("ALTER TABLE users ADD COLUMN notifications_enabled INTEGER DEFAULT 1")
            logger.info("Added notifications_enabled column")

        if "reminder_hour" not in columns:
            await conn.execute("ALTER TABLE users ADD COLUMN reminder_hour INTEGER DEFAULT 20")
            logger.info("Added reminder_hour column")

        if "last_reminder_sent" not in columns:
            await conn.execute("ALTER TABLE users ADD COLUMN last_reminder_sent TIMESTAMP")
            logger.info("Added last_reminder_sent column")

        await conn.commit()
