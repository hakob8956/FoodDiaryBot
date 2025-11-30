import json
from typing import Optional
from database.connection import db
from database.models import User, OnboardingState


class UserRepository:
    """Repository for user operations."""

    async def create_user(self, telegram_id: int, username: str = None, first_name: str = None) -> User:
        """Create a new user."""
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
        """Update user fields."""
        if not fields:
            return await self.get_user(telegram_id)

        set_clause = ", ".join(f"{k} = ?" for k in fields.keys())
        values = list(fields.values()) + [telegram_id]

        await db.execute(
            f"UPDATE users SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE telegram_id = ?",
            tuple(values)
        )
        return await self.get_user(telegram_id)

    async def set_onboarding_complete(self, telegram_id: int, daily_target: int) -> Optional[User]:
        """Mark user onboarding as complete with calculated calorie target."""
        return await self.update_user(
            telegram_id,
            daily_calorie_target=daily_target,
            onboarding_complete=1
        )

    async def set_calorie_override(self, telegram_id: int, calories: int) -> Optional[User]:
        """Set manual calorie override."""
        return await self.update_user(
            telegram_id,
            daily_calorie_target=calories,
            calorie_override=1
        )

    async def update_weight(self, telegram_id: int, weight: float) -> Optional[User]:
        """Update user weight."""
        return await self.update_user(telegram_id, weight=weight)

    # Onboarding state management

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

    async def save_onboarding_state(self, state: OnboardingState):
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

    async def clear_onboarding_state(self, telegram_id: int):
        """Remove onboarding state after completion."""
        await db.execute(
            "DELETE FROM onboarding_state WHERE telegram_id = ?",
            (telegram_id,)
        )


# Singleton instance
user_repo = UserRepository()
