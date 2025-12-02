from database.connection import db


SCHEMA_SQL = """
-- Users table
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
);

-- Onboarding state for multi-step registration
CREATE TABLE IF NOT EXISTS onboarding_state (
    telegram_id INTEGER PRIMARY KEY,
    current_step TEXT,
    collected_data TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Food logs table
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
);

-- Index for efficient date-based queries
CREATE INDEX IF NOT EXISTS idx_food_logs_user_date
ON food_logs(telegram_id, logged_at);
"""


async def run_migrations():
    """Create all database tables and run migrations."""
    async with db.get_connection() as conn:
        # Create tables
        await conn.executescript(SCHEMA_SQL)
        await conn.commit()

        # Run migrations for existing databases
        await _migrate_add_notification_columns(conn)

    print("Database migrations completed successfully.")


async def _migrate_add_notification_columns(conn):
    """Add notification columns to existing users table if missing."""
    # Check if columns exist
    cursor = await conn.execute("PRAGMA table_info(users)")
    columns = {row[1] for row in await cursor.fetchall()}

    # Add missing columns
    if "notifications_enabled" not in columns:
        await conn.execute("ALTER TABLE users ADD COLUMN notifications_enabled INTEGER DEFAULT 1")

    if "reminder_hour" not in columns:
        await conn.execute("ALTER TABLE users ADD COLUMN reminder_hour INTEGER DEFAULT 20")

    if "last_reminder_sent" not in columns:
        await conn.execute("ALTER TABLE users ADD COLUMN last_reminder_sent TIMESTAMP")

    await conn.commit()
