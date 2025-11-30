import json
from typing import Optional
from datetime import datetime, date
from database.connection import db
from database.models import FoodLog


class FoodLogRepository:
    """Repository for food log operations."""

    async def create_log(
        self,
        telegram_id: int,
        input_type: str,
        analysis_json: str,
        total_calories: int,
        total_protein: float,
        total_carbs: float,
        total_fat: float,
        confidence_score: float,
        raw_input: str = None,
        photo_file_id: str = None
    ) -> FoodLog:
        """Create a new food log entry."""
        cursor = await db.execute(
            """
            INSERT INTO food_logs (
                telegram_id, input_type, raw_input, photo_file_id,
                analysis_json, total_calories, total_protein,
                total_carbs, total_fat, confidence_score
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                telegram_id, input_type, raw_input, photo_file_id,
                analysis_json, total_calories, total_protein,
                total_carbs, total_fat, confidence_score
            )
        )
        return await self.get_log_by_id(cursor.lastrowid)

    async def get_log_by_id(self, log_id: int) -> Optional[FoodLog]:
        """Get a single food log by ID."""
        row = await db.fetch_one(
            "SELECT * FROM food_logs WHERE id = ?",
            (log_id,)
        )
        if row:
            return FoodLog(**row)
        return None

    async def get_logs_by_date(
        self,
        telegram_id: int,
        target_date: date
    ) -> list[FoodLog]:
        """Get all food logs for a specific date."""
        rows = await db.fetch_all(
            """
            SELECT * FROM food_logs
            WHERE telegram_id = ?
            AND date(logged_at) = date(?)
            ORDER BY logged_at ASC
            """,
            (telegram_id, target_date.isoformat())
        )
        return [FoodLog(**row) for row in rows]

    async def get_logs_by_date_range(
        self,
        telegram_id: int,
        start_date: date,
        end_date: date
    ) -> list[FoodLog]:
        """Get all food logs within a date range."""
        rows = await db.fetch_all(
            """
            SELECT * FROM food_logs
            WHERE telegram_id = ?
            AND date(logged_at) >= date(?)
            AND date(logged_at) <= date(?)
            ORDER BY logged_at ASC
            """,
            (telegram_id, start_date.isoformat(), end_date.isoformat())
        )
        return [FoodLog(**row) for row in rows]

    async def get_daily_totals(
        self,
        telegram_id: int,
        target_date: date
    ) -> dict:
        """Get aggregated totals for a specific date."""
        row = await db.fetch_one(
            """
            SELECT
                COALESCE(SUM(total_calories), 0) as calories,
                COALESCE(SUM(total_protein), 0) as protein,
                COALESCE(SUM(total_carbs), 0) as carbs,
                COALESCE(SUM(total_fat), 0) as fat,
                COUNT(*) as meal_count
            FROM food_logs
            WHERE telegram_id = ?
            AND date(logged_at) = date(?)
            """,
            (telegram_id, target_date.isoformat())
        )
        return dict(row) if row else {
            "calories": 0, "protein": 0, "carbs": 0, "fat": 0, "meal_count": 0
        }

    async def get_range_totals(
        self,
        telegram_id: int,
        start_date: date,
        end_date: date
    ) -> dict:
        """Get aggregated totals for a date range."""
        row = await db.fetch_one(
            """
            SELECT
                COALESCE(SUM(total_calories), 0) as calories,
                COALESCE(SUM(total_protein), 0) as protein,
                COALESCE(SUM(total_carbs), 0) as carbs,
                COALESCE(SUM(total_fat), 0) as fat,
                COUNT(*) as meal_count
            FROM food_logs
            WHERE telegram_id = ?
            AND date(logged_at) >= date(?)
            AND date(logged_at) <= date(?)
            """,
            (telegram_id, start_date.isoformat(), end_date.isoformat())
        )
        return dict(row) if row else {
            "calories": 0, "protein": 0, "carbs": 0, "fat": 0, "meal_count": 0
        }

    async def get_all_logs_json(self, telegram_id: int) -> list[dict]:
        """Get all logs as raw JSON for /rawlog command."""
        rows = await db.fetch_all(
            """
            SELECT id, logged_at, input_type, raw_input, analysis_json,
                   total_calories, total_protein, total_carbs, total_fat
            FROM food_logs
            WHERE telegram_id = ?
            ORDER BY logged_at DESC
            """,
            (telegram_id,)
        )
        result = []
        for row in rows:
            entry = dict(row)
            entry["analysis"] = json.loads(entry.pop("analysis_json"))
            result.append(entry)
        return result

    async def get_recent_logs(self, telegram_id: int, limit: int = 5) -> list[FoodLog]:
        """Get the most recent food logs for a user."""
        rows = await db.fetch_all(
            """
            SELECT * FROM food_logs
            WHERE telegram_id = ?
            ORDER BY logged_at DESC
            LIMIT ?
            """,
            (telegram_id, limit)
        )
        return [FoodLog(**row) for row in rows]

    async def delete_log(self, telegram_id: int, log_id: int) -> bool:
        """Delete a food log entry. Returns True if deleted, False if not found."""
        # First verify the log belongs to this user
        existing = await db.fetch_one(
            "SELECT id FROM food_logs WHERE id = ? AND telegram_id = ?",
            (log_id, telegram_id)
        )
        if not existing:
            return False

        await db.execute(
            "DELETE FROM food_logs WHERE id = ? AND telegram_id = ?",
            (log_id, telegram_id)
        )
        return True


# Singleton instance
food_log_repo = FoodLogRepository()
