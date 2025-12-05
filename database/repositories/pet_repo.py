"""
Pet repository.

Handles all database operations related to the pet/Tamagotchi system.
"""

from typing import Optional
from datetime import date

from database.connection import db
from database.models import PetStatus, Achievement


class PetRepository:
    """Repository for pet operations."""

    async def get_pet(self, telegram_id: int) -> Optional[PetStatus]:
        """Get pet status for a user."""
        row = await db.fetch_one(
            "SELECT * FROM pet_status WHERE telegram_id = ?",
            (telegram_id,)
        )
        if row:
            return PetStatus(**row)
        return None

    async def create_pet(
        self,
        telegram_id: int,
        pet_name: str = "Nibbles"
    ) -> PetStatus:
        """Create a new pet for a user."""
        await db.execute(
            """
            INSERT INTO pet_status (telegram_id, pet_name)
            VALUES (?, ?)
            ON CONFLICT(telegram_id) DO NOTHING
            """,
            (telegram_id, pet_name)
        )
        return await self.get_pet(telegram_id)

    async def get_or_create_pet(
        self,
        telegram_id: int,
        pet_name: str = "Nibbles"
    ) -> PetStatus:
        """Get existing pet or create a new one."""
        pet = await self.get_pet(telegram_id)
        if not pet:
            pet = await self.create_pet(telegram_id, pet_name)
        return pet

    async def feed_pet(self, telegram_id: int) -> PetStatus:
        """
        Record a meal being logged (feeding the pet).

        Updates total_meals_logged and streak counters.
        """
        today = date.today().isoformat()
        pet = await self.get_or_create_pet(telegram_id)

        # Calculate new streak
        new_streak = pet.current_streak
        if pet.last_fed_date:
            last_fed = date.fromisoformat(pet.last_fed_date)
            days_diff = (date.today() - last_fed).days

            if days_diff == 0:
                # Already fed today, streak stays the same
                pass
            elif days_diff == 1:
                # Fed yesterday, increment streak
                new_streak += 1
            else:
                # Missed days, reset streak
                new_streak = 1
        else:
            # First time feeding
            new_streak = 1

        # Update best streak if current is higher
        new_best = max(pet.best_streak, new_streak)

        await db.execute(
            """
            UPDATE pet_status
            SET total_meals_logged = total_meals_logged + 1,
                current_streak = ?,
                best_streak = ?,
                last_fed_date = ?
            WHERE telegram_id = ?
            """,
            (new_streak, new_best, today, telegram_id)
        )

        return await self.get_pet(telegram_id)

    async def rename_pet(self, telegram_id: int, new_name: str) -> PetStatus:
        """Rename the pet."""
        await db.execute(
            "UPDATE pet_status SET pet_name = ? WHERE telegram_id = ?",
            (new_name, telegram_id)
        )
        return await self.get_pet(telegram_id)

    async def set_meals(self, telegram_id: int, meals: int) -> PetStatus:
        """Set total meals logged (admin command for testing levels)."""
        await self.get_or_create_pet(telegram_id)
        await db.execute(
            "UPDATE pet_status SET total_meals_logged = ? WHERE telegram_id = ?",
            (meals, telegram_id)
        )
        return await self.get_pet(telegram_id)

    async def update_streak(self, telegram_id: int) -> PetStatus:
        """
        Update streak based on last_fed_date.

        Called on daily check to reset streak if user missed a day.
        """
        pet = await self.get_pet(telegram_id)
        if not pet or not pet.last_fed_date:
            return pet

        last_fed = date.fromisoformat(pet.last_fed_date)
        days_diff = (date.today() - last_fed).days

        if days_diff > 1:
            # Missed days, reset streak
            await db.execute(
                "UPDATE pet_status SET current_streak = 0 WHERE telegram_id = ?",
                (telegram_id,)
            )

        return await self.get_pet(telegram_id)

    # =========================================================================
    # ACHIEVEMENTS
    # =========================================================================

    async def get_achievements(self, telegram_id: int) -> list[Achievement]:
        """Get all achievements for a user."""
        rows = await db.fetch_all(
            "SELECT * FROM achievements WHERE telegram_id = ? ORDER BY unlocked_at DESC",
            (telegram_id,)
        )
        return [Achievement(**row) for row in rows]

    async def has_achievement(self, telegram_id: int, achievement_id: str) -> bool:
        """Check if user has a specific achievement."""
        row = await db.fetch_one(
            "SELECT 1 FROM achievements WHERE telegram_id = ? AND achievement_id = ?",
            (telegram_id, achievement_id)
        )
        return row is not None

    async def unlock_achievement(
        self,
        telegram_id: int,
        achievement_id: str
    ) -> Optional[Achievement]:
        """
        Unlock an achievement for a user.

        Returns the achievement if newly unlocked, None if already had it.
        """
        # Check if already unlocked
        if await self.has_achievement(telegram_id, achievement_id):
            return None

        await db.execute(
            """
            INSERT INTO achievements (telegram_id, achievement_id)
            VALUES (?, ?)
            ON CONFLICT(telegram_id, achievement_id) DO NOTHING
            """,
            (telegram_id, achievement_id)
        )

        # Fetch the newly created achievement
        row = await db.fetch_one(
            "SELECT * FROM achievements WHERE telegram_id = ? AND achievement_id = ?",
            (telegram_id, achievement_id)
        )
        return Achievement(**row) if row else None


# Singleton instance
pet_repo = PetRepository()
