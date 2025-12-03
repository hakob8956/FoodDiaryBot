"""
User repository.

Handles all database operations related to users and onboarding state.
"""

import json
from typing import Optional

from database.connection import db
from database.models import User, OnboardingState
from constants import REMINDER_HOUR_MIN, REMINDER_HOUR_MAX


class UserRepository:
    """Repository for user operations."""

    async def create_user(
        self,
        telegram_id: int,
        username: Optional[str] = None,
        first_name: Optional[str] = None
    ) -> User:
        """Create a new user or update existing."""
        await db.execute(
            """
            INSERT INTO users (telegram_id, username, first_name)
            VALUES (?, ?, ?)
            ON CONFLICT(telegram_id) DO UPDATE SET
                username = excluded.username,
                first_name = excluded.first_name,
                updated_at = CURRENT_TIMESTAMP
            """,
            (telegram_id, username, first_name)
        )
        return await self.get_user(telegram_id)

    async def get_user(self, telegram_id: int) -> Optional[User]:
        """Get user by telegram ID."""
        row = await db.fetch_one(
            "SELECT * FROM users WHERE telegram_id = ?",
            (telegram_id,)
        )
        if row:
            return User(**row)
        return None

    async def update_user(self, telegram_id: int, **fields) -> Optional[User]:
        """Update user fields dynamically."""
        if not fields:
            return await self.get_user(telegram_id)

        set_clause = ", ".join(f"{k} = ?" for k in fields.keys())
        values = list(fields.values()) + [telegram_id]

        await db.execute(
            f"UPDATE users SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE telegram_id = ?",
            tuple(values)
        )
        return await self.get_user(telegram_id)

    async def set_onboarding_complete(
        self,
        telegram_id: int,
        daily_target: int
    ) -> Optional[User]:
        """Mark user onboarding as complete with calculated calorie target."""
        return await self.update_user(
            telegram_id,
            daily_calorie_target=daily_target,
            onboarding_complete=1
        )

    async def set_calorie_override(
        self,
        telegram_id: int,
        calories: int
    ) -> Optional[User]:
        """Set manual calorie override."""
        return await self.update_user(
            telegram_id,
            daily_calorie_target=calories,
            calorie_override=1
        )

    async def update_weight(self, telegram_id: int, weight: float) -> Optional[User]:
        """Update user weight."""
        return await self.update_user(telegram_id, weight=weight)

    # =========================================================================
    # ONBOARDING STATE MANAGEMENT
    # =========================================================================

    async def get_onboarding_state(self, telegram_id: int) -> Optional[OnboardingState]:
        """Get current onboarding state."""
        row = await db.fetch_one(
            "SELECT * FROM onboarding_state WHERE telegram_id = ?",
            (telegram_id,)
        )
        if row:
            data = row.copy()
            data["collected_data"] = json.loads(data.get("collected_data") or "{}")
            return OnboardingState(**data)
        return None

    async def save_onboarding_state(self, state: OnboardingState) -> None:
        """Save or update onboarding state."""
        await db.execute(
            """
            INSERT INTO onboarding_state (telegram_id, current_step, collected_data)
            VALUES (?, ?, ?)
            ON CONFLICT(telegram_id) DO UPDATE SET
                current_step = excluded.current_step,
                collected_data = excluded.collected_data,
                updated_at = CURRENT_TIMESTAMP
            """,
            (state.telegram_id, state.current_step, json.dumps(state.collected_data))
        )

    async def clear_onboarding_state(self, telegram_id: int) -> None:
        """Remove onboarding state after completion."""
        await db.execute(
            "DELETE FROM onboarding_state WHERE telegram_id = ?",
            (telegram_id,)
        )

    # =========================================================================
    # NOTIFICATION METHODS
    # =========================================================================

    async def get_users_for_reminder(self, current_hour: int) -> list[User]:
        """
        Get users eligible for reminder notification.

        Returns users who:
        - Have completed onboarding
        - Have notifications enabled
        - Have reminder_hour matching current hour
        - Haven't been reminded today
        """
        rows = await db.fetch_all(
            """
            SELECT * FROM users
            WHERE onboarding_complete = 1
            AND notifications_enabled = 1
            AND reminder_hour = ?
            AND (
                last_reminder_sent IS NULL
                OR date(last_reminder_sent) < date('now')
            )
            """,
            (current_hour,)
        )
        return [User(**row) for row in rows]

    async def update_last_reminder(self, telegram_id: int) -> None:
        """Update the last_reminder_sent timestamp."""
        await db.execute(
            "UPDATE users SET last_reminder_sent = CURRENT_TIMESTAMP WHERE telegram_id = ?",
            (telegram_id,)
        )

    async def set_notifications_enabled(
        self,
        telegram_id: int,
        enabled: bool
    ) -> Optional[User]:
        """Enable or disable notifications for a user."""
        return await self.update_user(
            telegram_id,
            notifications_enabled=1 if enabled else 0
        )

    async def set_reminder_hour(
        self,
        telegram_id: int,
        hour: int
    ) -> Optional[User]:
        """Set the preferred reminder hour."""
        if not REMINDER_HOUR_MIN <= hour <= REMINDER_HOUR_MAX:
            raise ValueError(
                f"Hour must be between {REMINDER_HOUR_MIN} and {REMINDER_HOUR_MAX}"
            )
        return await self.update_user(telegram_id, reminder_hour=hour)


# Singleton instance
user_repo = UserRepository()
