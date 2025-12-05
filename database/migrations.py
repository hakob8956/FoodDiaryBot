"""
Database migrations.

Handles table creation and schema updates for both SQLite and Turso backends.
Uses constants for default values to avoid hardcoding.
"""

import logging

from database.connection import db, SQLiteDatabase, TursoDatabase
from constants import (
    Sex,
    ActivityLevel,
    Goal,
    InputType,
    DEFAULT_REMINDER_HOUR,
)

logger = logging.getLogger(__name__)


# =============================================================================
# TABLE SCHEMAS
# =============================================================================

# Build CHECK constraints from enums
SEX_VALUES = ", ".join(f"'{s.value}'" for s in Sex)
ACTIVITY_VALUES = ", ".join(f"'{a.value}'" for a in ActivityLevel)
GOAL_VALUES = ", ".join(f"'{g.value}'" for g in Goal)
INPUT_TYPE_VALUES = ", ".join(f"'{i.value}'" for i in InputType)

CREATE_USERS_TABLE = f"""
CREATE TABLE IF NOT EXISTS users (
    telegram_id INTEGER PRIMARY KEY,
    username TEXT,
    first_name TEXT,
    weight REAL,
    height REAL,
    age INTEGER,
    sex TEXT CHECK(sex IN ({SEX_VALUES})),
    activity_level TEXT CHECK(activity_level IN ({ACTIVITY_VALUES})),
    goal TEXT CHECK(goal IN ({GOAL_VALUES})),
    daily_calorie_target INTEGER,
    calorie_override INTEGER DEFAULT 0,
    onboarding_complete INTEGER DEFAULT 0,
    notifications_enabled INTEGER DEFAULT 1,
    reminder_hour INTEGER DEFAULT {DEFAULT_REMINDER_HOUR},
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

CREATE_FOOD_LOGS_TABLE = f"""
CREATE TABLE IF NOT EXISTS food_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id INTEGER NOT NULL,
    logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    input_type TEXT CHECK(input_type IN ({INPUT_TYPE_VALUES})),
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

CREATE_PET_STATUS_TABLE = """
CREATE TABLE IF NOT EXISTS pet_status (
    telegram_id INTEGER PRIMARY KEY,
    pet_name TEXT DEFAULT 'Nibbles',
    total_meals_logged INTEGER DEFAULT 0,
    current_streak INTEGER DEFAULT 0,
    best_streak INTEGER DEFAULT 0,
    last_fed_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (telegram_id) REFERENCES users(telegram_id)
)
"""

CREATE_ACHIEVEMENTS_TABLE = """
CREATE TABLE IF NOT EXISTS achievements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id INTEGER NOT NULL,
    achievement_id TEXT NOT NULL,
    unlocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(telegram_id, achievement_id),
    FOREIGN KEY (telegram_id) REFERENCES users(telegram_id)
)
"""


# =============================================================================
# MIGRATION FUNCTIONS
# =============================================================================

async def run_migrations() -> None:
    """Create all database tables and run migrations."""
    logger.info("Running database migrations...")

    # Create tables one by one (works with both SQLite and Turso)
    statements = [
        CREATE_USERS_TABLE,
        CREATE_ONBOARDING_STATE_TABLE,
        CREATE_FOOD_LOGS_TABLE,
        CREATE_FOOD_LOGS_INDEX,
        CREATE_PET_STATUS_TABLE,
        CREATE_ACHIEVEMENTS_TABLE,
    ]

    await db.execute_many(statements)

    # Run additional migrations for existing databases
    await _migrate_add_notification_columns()
    await _migrate_add_macro_columns()
    await _migrate_update_goal_constraint()
    await _migrate_add_weekly_summary_columns()

    logger.info("Database migrations completed successfully.")


async def _migrate_add_notification_columns() -> None:
    """Add notification columns to existing users table if missing."""
    columns_to_add = [
        ("notifications_enabled", "INTEGER DEFAULT 1"),
        ("reminder_hour", f"INTEGER DEFAULT {DEFAULT_REMINDER_HOUR}"),
        ("last_reminder_sent", "TIMESTAMP"),
    ]

    if isinstance(db, TursoDatabase):
        await _migrate_columns_turso(columns_to_add)
    else:
        await _migrate_columns_sqlite(columns_to_add)


async def _migrate_columns_turso(columns: list[tuple[str, str]]) -> None:
    """Add columns for Turso (try/except for each)."""
    for col_name, col_type in columns:
        try:
            await db.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}")
            logger.info(f"Added column {col_name} to users table")
        except Exception as e:
            error_msg = str(e).lower()
            # Column likely already exists - this is expected
            if "duplicate column" in error_msg or "already exists" in error_msg:
                logger.debug(f"Column {col_name} already exists")
            else:
                logger.warning(f"Could not add column {col_name}: {e}")


async def _migrate_columns_sqlite(columns: list[tuple[str, str]]) -> None:
    """Add columns for SQLite (uses PRAGMA to check existing columns)."""
    # Get existing columns
    rows = await db.fetch_all("PRAGMA table_info(users)")
    existing_columns = {row['name'] for row in rows}

    # Add missing columns
    for col_name, col_type in columns:
        if col_name not in existing_columns:
            try:
                await db.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}")
                logger.info(f"Added column {col_name} to users table")
            except Exception as e:
                logger.warning(f"Could not add column {col_name}: {e}")


async def _migrate_add_macro_columns() -> None:
    """Add macro target columns to existing users table if missing."""
    columns_to_add = [
        ("protein_target", "INTEGER"),
        ("carbs_target", "INTEGER"),
        ("fat_target", "INTEGER"),
        ("macro_override", "INTEGER DEFAULT 0"),
    ]

    if isinstance(db, TursoDatabase):
        await _migrate_columns_turso(columns_to_add)
    else:
        await _migrate_columns_sqlite(columns_to_add)


async def _migrate_update_goal_constraint() -> None:
    """
    Update the goal CHECK constraint to include 'gain_muscles'.

    SQLite/Turso don't support ALTER CONSTRAINT, so we need to recreate the table.
    This migration backs up data, recreates the table, and restores data.
    """
    try:
        # Check if constraint needs updating by trying to find gain_muscles
        rows = await db.fetch_all("SELECT sql FROM sqlite_master WHERE type='table' AND name='users'")
        if not rows:
            return

        table_sql = rows[0].get('sql', '') if rows[0] else ''
        if "'gain_muscles'" in table_sql:
            # Constraint already includes gain_muscles
            return

        logger.info("Updating goal CHECK constraint to include 'gain_muscles'...")

        # Recreate table with updated constraint
        await db.execute("PRAGMA foreign_keys=OFF")

        # Create new table with updated constraint
        await db.execute(f"""
            CREATE TABLE IF NOT EXISTS users_new (
                telegram_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                weight REAL,
                height REAL,
                age INTEGER,
                sex TEXT CHECK(sex IN ({SEX_VALUES})),
                activity_level TEXT CHECK(activity_level IN ({ACTIVITY_VALUES})),
                goal TEXT CHECK(goal IN ({GOAL_VALUES})),
                daily_calorie_target INTEGER,
                calorie_override INTEGER DEFAULT 0,
                protein_target INTEGER,
                carbs_target INTEGER,
                fat_target INTEGER,
                macro_override INTEGER DEFAULT 0,
                onboarding_complete INTEGER DEFAULT 0,
                notifications_enabled INTEGER DEFAULT 1,
                reminder_hour INTEGER DEFAULT {DEFAULT_REMINDER_HOUR},
                last_reminder_sent TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Copy data from old table
        await db.execute("""
            INSERT INTO users_new
            SELECT
                telegram_id, username, first_name, weight, height, age, sex,
                activity_level, goal, daily_calorie_target, calorie_override,
                COALESCE(protein_target, NULL),
                COALESCE(carbs_target, NULL),
                COALESCE(fat_target, NULL),
                COALESCE(macro_override, 0),
                onboarding_complete, notifications_enabled, reminder_hour,
                last_reminder_sent, created_at, updated_at
            FROM users
        """)

        # Drop old table and rename new one
        await db.execute("DROP TABLE users")
        await db.execute("ALTER TABLE users_new RENAME TO users")

        await db.execute("PRAGMA foreign_keys=ON")

        logger.info("Goal CHECK constraint updated successfully")

    except Exception as e:
        logger.warning(f"Could not update goal constraint: {e}")


async def _migrate_add_weekly_summary_columns() -> None:
    """Add weekly summary columns to existing users table if missing."""
    columns_to_add = [
        ("weekly_summary_enabled", "INTEGER DEFAULT 1"),
        ("last_weekly_summary_sent", "TIMESTAMP"),
    ]

    if isinstance(db, TursoDatabase):
        await _migrate_columns_turso(columns_to_add)
    else:
        await _migrate_columns_sqlite(columns_to_add)
